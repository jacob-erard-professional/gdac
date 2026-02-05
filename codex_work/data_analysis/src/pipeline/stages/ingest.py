import csv
from src.pipeline.schema import validate_columns, validate_row
from src.pipeline.stage_runtime import make_manifest
from src.utils.io import write_csv


def run(config):
    raw_files = sorted(config.raw_dir.glob('*.csv'))
    rows = []
    bad = 0
    for fp in raw_files:
        with fp.open(newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            ok, missing = validate_columns(reader.fieldnames or [])
            if not ok:
                raise ValueError(f'Missing columns {missing} in {fp}')
            for r in reader:
                if validate_row(r):
                    rows.append(r)
                else:
                    bad += 1
    rows = sorted(rows, key=lambda r: (r.get('id') or r.get('tweet_id', ''), r.get('created_at', '')))
    out = config.processed_dir / 'ingested.csv'
    fields = sorted({k for r in rows for k in r.keys()}) if rows else ['id', 'author_id', 'created_at', 'text']
    write_csv(out, rows, fields)
    return make_manifest(raw_files, [out], len(rows) + bad, len(rows), notes=[f'invalid_rows={bad}'])
