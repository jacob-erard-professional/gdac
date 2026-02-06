import json
from pathlib import Path

import pandas as pd

from src.sentiment.parent_company_deep_impact import run_parent_company_deep_sentiment_analysis


def test_parent_company_deep_sentiment_join_and_summary(tmp_path: Path):
    deep_dir = tmp_path / "sentiment" / "deep" / "2024"
    deep_dir.mkdir(parents=True, exist_ok=True)
    deep_path = deep_dir / "deep_sentiment.json"
    deep_path.write_text(
        json.dumps(
            {
                "metadata": {"model_id": "x"},
                "records": [
                    {
                        "tweet_id": "1",
                        "year": 2024,
                        "text": "great ad",
                        "main_sentiment": "joy",
                        "confidence": 0.9,
                        "pipeline_row_id": "1",
                    },
                    {
                        "tweet_id": "2",
                        "year": 2024,
                        "text": "bad ad",
                        "main_sentiment": "anger",
                        "confidence": 0.8,
                        "pipeline_row_id": "2",
                    },
                    {
                        "tweet_id": "3",
                        "year": 2024,
                        "text": "ok ad",
                        "main_sentiment": "neutral",
                        "confidence": 0.6,
                        "pipeline_row_id": "3",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    enriched_path = tmp_path / "data" / "enriched" / "2024" / "enriched.csv"
    enriched_path.parent.mkdir(parents=True, exist_ok=True)
    enriched_path.write_text(
        "id,ad_tag,brand_tag,game_phase,pipeline_row_id,created_at_utc\n"
        "1,ad_a,brand_a,pre,1,2024-02-11T10:00:00Z\n"
        "2,ad_a,brand_a,pre,2,2024-02-11T10:10:00Z\n"
        "3,ad_b,brand_b,in,3,2024-02-11T10:30:00Z\n",
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
    outputs, manifest = run_parent_company_deep_sentiment_analysis(
        year=2024,
        deep_sentiment_path=deep_path,
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
    assert manifest.record_counts["input"] == 3
    assert manifest.record_counts["output"] == 3

    joined = pd.read_parquet(outputs.joined_parquet)
    assert list(joined["tweet_id"]) == ["1", "2", "3"]

    summary = json.loads(outputs.summary_json.read_text(encoding="utf-8"))
    assert summary["matched_rows"] == 3
    parent_a = next(item for item in summary["parents"] if item["parent_company"] == "parent_a")
    assert parent_a["tweet_count"] == 2
    assert parent_a["joy_count"] == 1

    time_slices = json.loads(outputs.timeslices_json.read_text(encoding="utf-8"))
    assert time_slices["time_slice_minutes"] == 15
    assert time_slices["time_slices"]
