"""Pipeline module for process orchestration and execution."""

import csv
import re
from src.pipeline.stage_runtime import make_manifest
from src.utils.io import write_csv

HASHTAG_RE = re.compile(r"#(\w+)")
WORD_RE = re.compile(r"[A-Za-z0-9_]+")


def _sentiment(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ['love', 'great', 'win']):
        return 'positive'
    if any(w in t for w in ['bad', 'hate', 'lose']):
        return 'negative'
    return 'neutral'


def run(config):
    in_file = config.processed_dir / 'cleaned.csv'
    out_file = config.enriched_dir / 'enriched.csv'
    enriched = []
    with in_file.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = row.get('text', '')
            hashtags = HASHTAG_RE.findall(text)
            words = [w.lower() for w in WORD_RE.findall(text)]
            row['hashtags'] = '|'.join(sorted(set(hashtags)))
            row['keywords'] = '|'.join(sorted(set(words[:25])))
            brand = (
                row.get('brand')
                or row.get('brand_ad_name')
                or row.get('brand_hint')
                or ''
            )
            row['brand'] = str(brand).strip()
            row['brand_tag'] = row['brand'].lower() if row['brand'] else 'unknown_brand'
            row['ad_tag'] = row.get('brand_ad_name') or row.get('ad_hint') or row.get('brand') or 'unknown_ad'
            row['sentiment_label'] = _sentiment(text)
            row['sentiment_score'] = {'negative': -1, 'neutral': 0, 'positive': 1}[row['sentiment_label']]
            row['game_phase'] = row.get('game_phase') or 'unknown'
            enriched.append(row)
    fields = sorted({k for r in enriched for k in r.keys()}) if enriched else []
    write_csv(out_file, enriched, fields)
    return make_manifest([in_file], [out_file], len(enriched), len(enriched))
