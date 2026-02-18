"""Tests for test bertweet sentiment core behavior."""

from pathlib import Path

import pytest

from src.sentiment.bertweet import (
    load_input_rows,
    preprocess_tweet_text,
    validate_label_mapping,
    write_sentiment_augmented_csv,
)


def test_preprocess_removes_urls_and_normalizes_whitespace_only():
    text = "Wow   https://example.com   #SuperBowl  😄"
    processed = preprocess_tweet_text(text)
    assert processed == "Wow #SuperBowl 😄"


def test_validate_label_mapping_accepts_common_bertweet_labels():
    canonical = validate_label_mapping({0: "NEG", 1: "NEU", 2: "POS"})
    assert canonical == {0: "negative", 1: "neutral", 2: "positive"}


def test_validate_label_mapping_rejects_missing_required_labels():
    with pytest.raises(ValueError):
        validate_label_mapping({0: "NEG", 1: "POS"})


def test_load_input_rows_supports_id_column_and_derived_year(tmp_path: Path):
    input_path = tmp_path / "cleaned.csv"
    input_path.write_text(
        "id,text,created_at\n"
        "2,second,2024-01-02 10:00:00\n"
        "1,first,2024-01-01 09:00:00\n",
        encoding="utf-8",
    )

    rows, invalid = load_input_rows(input_path, target_year=2024)

    assert invalid == 0
    assert [row["tweet_id"] for row in rows] == ["1", "2"]
    assert all(row["year"] == 2024 for row in rows)


def test_write_sentiment_augmented_csv_appends_columns(tmp_path: Path):
    input_path = tmp_path / "cleaned.csv"
    output_path = tmp_path / "tweets_with_sentiement.csv"
    input_path.write_text(
        "id,text,pipeline_row_id,brand\n"
        "10,hello,1,BrandA\n"
        "11,world,2,BrandB\n",
        encoding="utf-8",
    )
    records = [
        {"tweet_id": "10", "pipeline_row_id": "1", "sentiment": "positive", "confidence": 0.9},
        {"tweet_id": "11", "pipeline_row_id": "2", "sentiment": "neutral", "confidence": 0.5},
    ]

    write_sentiment_augmented_csv(output_path=output_path, input_path=input_path, records=records)

    content = output_path.read_text(encoding="utf-8").strip().splitlines()
    assert content[0] == "id,text,pipeline_row_id,brand,sentiment,confidence"
    assert content[1].endswith(",positive,0.9")
    assert content[2].endswith(",neutral,0.5")
