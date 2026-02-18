"""Tests for test ad sentiment core behavior."""

import json
from pathlib import Path

import pandas as pd

from src.sentiment.ad_impact import run_ad_sentiment_analysis


def test_ad_sentiment_join_and_summary(tmp_path: Path):
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
        "id,ad_tag,brand_tag,game_phase\n"
        "1,ad_a,brand_a,pre\n"
        "2,ad_a,brand_a,pre\n"
        "3,ad_b,brand_b,in\n",
        encoding="utf-8",
    )

    out_dir = tmp_path / "outputs" / "analytics" / "2024"
    outputs, manifest = run_ad_sentiment_analysis(
        year=2024,
        sentiment_path=sentiment_path,
        enriched_path=enriched_path,
        output_dir=out_dir,
        min_tweets=1,
    )

    assert outputs.joined_parquet.exists()
    assert outputs.summary_json.exists()
    assert outputs.summary_csv.exists()
    assert manifest.record_counts["input"] == 3
    assert manifest.record_counts["output"] == 3

    joined = pd.read_parquet(outputs.joined_parquet)
    assert list(joined["tweet_id"]) == ["1", "2", "3"]

    summary = json.loads(outputs.summary_json.read_text(encoding="utf-8"))
    assert summary["matched_rows"] == 3
    ad_a = next(item for item in summary["ads"] if item["ad_tag"] == "ad_a")
    assert ad_a["tweet_count"] == 2
    assert ad_a["net_sentiment"] == 0.0
