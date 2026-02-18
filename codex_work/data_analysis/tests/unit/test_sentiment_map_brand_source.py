"""Tests for test sentiment map brand source behavior."""

import json
from pathlib import Path

from src.scripts.match_sentiment_to_companies import run_match_sentiment_to_companies


def test_sentiment_map_uses_record_brand_over_hashtag_mapping(tmp_path: Path):
    sentiment_file = tmp_path / "sentiment.json"
    brand_groups_file = tmp_path / "brand_groups.json"
    parent_groups_file = tmp_path / "parent_groups.json"
    output_file = tmp_path / "sentiment_company_map.jsonl"

    sentiment_file.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "tweet_id": "1",
                        "pipeline_row_id": "1",
                        "year": 2024,
                        "text": "Watch this #foo now",
                        "brand": "pepsico",
                        "sentiment": "positive",
                        "confidence": 0.99,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    brand_groups_file.write_text(
        json.dumps(
            {
                "brands": [
                    {
                        "brand": "cocacola",
                        "hashtags": [{"hashtag": "foo", "count": 10}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    parent_groups_file.write_text(
        json.dumps(
            {
                "parent_companies": [
                    {"parent_company": "pepsico_parent", "brands": [{"brand": "pepsico"}]},
                    {"parent_company": "coke_parent", "brands": [{"brand": "cocacola"}]},
                ]
            }
        ),
        encoding="utf-8",
    )

    out_path = run_match_sentiment_to_companies(
        sentiment_file=sentiment_file,
        brand_groups_file=brand_groups_file,
        parent_groups_file=parent_groups_file,
        output_file=output_file,
        batch_size=1000,
    )

    payload = json.loads(out_path.read_text(encoding="utf-8").strip())
    record = payload["records"][0]
    assert record["primary_brand"] == "pepsico"
    assert record["primary_parent_company"] == "pepsico_parent"
