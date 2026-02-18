"""Tests for test parent company sentiment core behavior."""

import json
from pathlib import Path

import pandas as pd

from src.sentiment.parent_company_impact import run_parent_company_sentiment_analysis


def test_parent_company_sentiment_join_and_summary(tmp_path: Path):
    sentiment_dir = tmp_path / "sentiment" / "bertweet" / "2024"
    sentiment_dir.mkdir(parents=True, exist_ok=True)
    sentiment_path = sentiment_dir / "sentiment.json"
    sentiment_path.write_text(
        json.dumps(
            {
                "metadata": {"model_id": "x"},
                "records": [
                    {"tweet_id": "1", "year": 2024, "text": "great ad", "sentiment": "positive", "confidence": 0.9},
                    {"tweet_id": "2", "year": 2024, "text": "bad ad", "sentiment": "negative", "confidence": 0.8},
                    {"tweet_id": "3", "year": 2024, "text": "ok ad", "sentiment": "neutral", "confidence": 0.6},
                ],
            }
        ),
        encoding="utf-8",
    )

    enriched_path = tmp_path / "data" / "enriched" / "2024" / "enriched.csv"
    enriched_path.parent.mkdir(parents=True, exist_ok=True)
    enriched_path.write_text(
        "id,brand_tag,ad_tag,game_phase,created_at_utc\n"
        "1,brand_a,ad_a,pre,2024-02-11T10:00:00Z\n"
        "2,brand_a,ad_a,pre,2024-02-11T10:10:00Z\n"
        "3,brand_b,ad_b,in,2024-02-11T10:30:00Z\n",
        encoding="utf-8",
    )

    parent_groups_path = tmp_path / "outputs" / "analytics" / "2024" / "parent_company_groups.json"
    parent_groups_path.parent.mkdir(parents=True, exist_ok=True)
    parent_groups_path.write_text(
        json.dumps(
            {
                "year": "2024",
                "parent_companies": [
                    {
                        "parent_company": "parent_a",
                        "brands": [
                            {"brand": "brand_a", "total_count": 10, "hashtags": []}
                        ],
                    },
                    {
                        "parent_company": "parent_b",
                        "brands": [
                            {"brand": "brand_b", "total_count": 5, "hashtags": []}
                        ],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    out_dir = tmp_path / "outputs" / "analytics" / "2024"
    outputs, manifest = run_parent_company_sentiment_analysis(
        year=2024,
        sentiment_path=sentiment_path,
        enriched_path=enriched_path,
        parent_groups_path=parent_groups_path,
        output_dir=out_dir,
        min_tweets=1,
    )

    assert outputs.joined_parquet.exists()
    assert outputs.summary_json.exists()
    assert outputs.summary_csv.exists()
    assert outputs.timeslices_json.exists()
    assert outputs.timeslices_csv.exists()
    assert outputs.ad_tag_json.exists()
    assert outputs.ad_tag_csv.exists()
    assert manifest.record_counts["input"] == 3
    assert manifest.record_counts["output"] == 3

    joined = pd.read_parquet(outputs.joined_parquet)
    assert list(joined["tweet_id"]) == ["1", "2", "3"]

    summary = json.loads(outputs.summary_json.read_text(encoding="utf-8"))
    assert summary["matched_rows"] == 3
    parent_a = next(item for item in summary["parents"] if item["parent_company"] == "parent_a")
    assert parent_a["tweet_count"] == 2
    assert parent_a["net_sentiment"] == 0.0
    assert "weighted_lift_vs_overall" in parent_a

    time_slices = json.loads(outputs.timeslices_json.read_text(encoding="utf-8"))
    assert time_slices["time_slice_minutes"] == 15
    assert time_slices["time_slices"]

    ad_tag_summary = json.loads(outputs.ad_tag_json.read_text(encoding="utf-8"))
    assert ad_tag_summary["groups"]
    group = next(item for item in ad_tag_summary["groups"] if item["ad_tag"] == "ad_a")
    assert group["parent_company"] == "parent_a"
