import csv
from datetime import datetime
from src.pipeline.stage_runtime import make_manifest
from src.utils.io import write_csv


def _normalize_ts(value: str) -> str:
    if not value:
        return ''
    for fmt in ('%Y-%m-%d %H:%M:%S', '%a %b %d %H:%M:%S %z %Y'):
        try:
            return datetime.strptime(value, fmt).isoformat()
        except ValueError:
            continue
    return value


def run(config):
    in_file = config.processed_dir / 'ingested.csv'
    out_file = config.processed_dir / 'cleaned.csv'
    seen = set()
    cleaned = []
    with in_file.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tid = row.get('tweet_id')
            if tid in seen:
                continue
            seen.add(tid)
            row['created_at_utc'] = _normalize_ts(row.get('created_at', ''))
            row['text_original'] = row.get('text', '')
            row['text'] = (row.get('text') or '').strip()
            row['cleaning_flags'] = '' if row['text'] else 'empty_text'
            cleaned.append(row)
    fields = sorted({k for r in cleaned for k in r.keys()}) if cleaned else []
    write_csv(out_file, cleaned, fields)
    return make_manifest([in_file], [out_file], len(cleaned), len(cleaned))
