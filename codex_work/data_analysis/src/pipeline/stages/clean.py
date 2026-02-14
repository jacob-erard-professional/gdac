import csv
from datetime import datetime
from src.pipeline.stage_runtime import make_manifest
from src.utils.io import write_csv

TARGET_COLUMNS = [
    'id',
    'author_id',
    'created_at',
    'conversation_id',
    'brand',
    'brand_ad_name',
    'team_name',
    'text',
    'lang',
    'possibly_sensitive',
    'entities.hashtags',
    'entities.urls',
    'referenced_tweets',
    'in_reply_to_user_id',
    'public_metrics.retweet_count',
    'public_metrics.reply_count',
    'public_metrics.like_count',
    'public_metrics.quote_count',
    'public_metrics.bookmark_count',
    'username',
    'name',
]


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
    row_index = 0
    with in_file.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tid = row.get('id') or row.get('tweet_id')
            if tid in seen:
                continue
            seen.add(tid)
            text = (row.get('text') or '').strip()
            normalized = {k: row.get(k, '') for k in TARGET_COLUMNS}
            normalized['id'] = normalized['id'] or row.get('tweet_id', '')
            normalized['author_id'] = normalized['author_id'] or row.get('user_id', '')
            normalized['brand'] = (
                row.get('brand')
                or row.get('brand_ad_name')
                or row.get('team_name')
                or row.get('brand_tag')
                or ''
            )
            normalized['text'] = text
            row_index += 1
            normalized['pipeline_row_id'] = str(row_index)
            normalized['created_at_utc'] = _normalize_ts(row.get('created_at', ''))
            normalized['text_original'] = row.get('text', '')
            normalized['cleaning_flags'] = '' if text else 'empty_text'
            cleaned.append(normalized)
    fields = TARGET_COLUMNS + ['pipeline_row_id', 'created_at_utc', 'text_original', 'cleaning_flags']
    write_csv(out_file, cleaned, fields)
    return make_manifest([in_file], [out_file], len(cleaned), len(cleaned))
