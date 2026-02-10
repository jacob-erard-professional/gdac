from __future__ import annotations

import ast
import csv
import json
from typing import Any, Dict, Iterable, List

from src.models.schemas import TweetRecord, normalize_text

JSON_LIKE_COLUMNS = {
    "referenced_tweets",
    "entities.annotations",
    "entities.mentions",
    "entities.hashtags",
    "entities.cashtags",
    "entities.urls",
}

METRIC_COLUMNS = {
    "public_metrics.retweet_count",
    "public_metrics.reply_count",
    "public_metrics.like_count",
    "public_metrics.quote_count",
    "public_metrics.bookmark_count",
    "public_metrics.impression_count",
}


def parse_json_like(value: Any) -> List[Dict[str, Any]]:
    if value is None:
        return []
    text = str(value).strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        try:
            parsed = ast.literal_eval(text)
        except (ValueError, SyntaxError):
            return []
    if isinstance(parsed, list):
        return [item for item in parsed if isinstance(item, dict)]
    return []


def parse_int(value: Any) -> int:
    if value is None:
        return 0
    text = str(value).strip()
    if not text:
        return 0
    try:
        return int(float(text))
    except ValueError:
        return 0


def read_csv_rows(path: str) -> Iterable[Dict[str, Any]]:
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield row


def parse_row(row: Dict[str, Any]) -> TweetRecord:
    text = normalize_text(row.get("text"))
    brand = normalize_text(row.get("brand"))
    annotations = parse_json_like(row.get("entities.annotations"))
    mentions = parse_json_like(row.get("entities.mentions"))
    hashtags = parse_json_like(row.get("entities.hashtags"))
    cashtags = parse_json_like(row.get("entities.cashtags"))
    urls = parse_json_like(row.get("entities.urls"))
    referenced_tweets = parse_json_like(row.get("referenced_tweets"))

    metrics = {key: parse_int(row.get(key)) for key in METRIC_COLUMNS}

    metadata = {
        key: value
        for key, value in row.items()
        if key
        not in {
            "text",
            "brand",
            *JSON_LIKE_COLUMNS,
            *METRIC_COLUMNS,
        }
    }

    return TweetRecord(
        text=text,
        brand=brand,
        metadata=metadata,
        annotations=annotations,
        mentions=mentions,
        hashtags=hashtags,
        cashtags=cashtags,
        urls=urls,
        referenced_tweets=referenced_tweets,
        public_metrics=metrics,
    )


def write_csv(path: str, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
