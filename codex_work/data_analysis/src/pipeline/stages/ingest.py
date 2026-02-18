"""Pipeline module for ingest orchestration and execution."""

import csv
from src.pipeline.schema import validate_columns, validate_row
from src.pipeline.stage_runtime import make_manifest
from src.utils.io import write_csv


def _normalized_key(key: str) -> str:
    return " ".join(str(key or "").strip().lower().split())


def _canonical_column_name(raw_name: str) -> str:
    normalized = _normalized_key(raw_name)
    aliases = {
        "tweet_id": "id",
        "user_id": "author_id",
        "created at": "created_at",
        "created_at, zulu time": "created_at",
    }
    return aliases.get(normalized, str(raw_name or "").strip())


def _canonicalize_row(row: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in row.items():
        canonical = _canonical_column_name(key)
        existing = out.get(canonical, "")
        if existing in ("", None):
            out[canonical] = value
    return out


def run(config):
    raw_files = sorted(config.raw_dir.glob('*.csv'))
    rows = []
    bad = 0
    for fp in raw_files:
        with fp.open(newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            canonical_fields = [_canonical_column_name(name) for name in (reader.fieldnames or [])]
            ok, missing = validate_columns(canonical_fields)
            if not ok:
                raise ValueError(f'Missing columns {missing} in {fp}')
            for r in reader:
                row = _canonicalize_row(r)
                if validate_row(row):
                    rows.append(row)
                else:
                    bad += 1
    rows = sorted(rows, key=lambda r: (r.get('id') or r.get('tweet_id', ''), r.get('created_at', '')))
    out = config.processed_dir / 'ingested.csv'
    fields = sorted({k for r in rows for k in r.keys()}) if rows else ['id', 'author_id', 'created_at', 'text']
    write_csv(out, rows, fields)
    return make_manifest(raw_files, [out], len(rows) + bad, len(rows), notes=[f'invalid_rows={bad}'])
