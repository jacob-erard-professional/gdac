import json
from collections import Counter
from pathlib import Path

from src.agents.sentiment.validation import validate_record, validate_summary


def write_records(out_path: Path, records: list[dict]) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    stable_records = sorted(records, key=lambda r: str(r.get("tweet_id", "")))
    with out_path.open("w", encoding="utf-8") as f:
        for record in stable_records:
            validate_record(record)
            f.write(json.dumps(record, sort_keys=True) + "\n")
    return out_path


def write_summary(out_path: Path, year: int, records: list[dict]) -> Path:
    sentiments = Counter(r["final"]["sentiment"] for r in records)
    emotions = Counter(r["agents"]["emotion"]["emotion"] for r in records)
    sarcasm_count = sum(1 for r in records if r["agents"]["sarcasm"]["is_sarcastic"])
    low_confidence_count = sum(1 for r in records if "low_confidence" in r.get("flags", []))
    total = len(records)
    summary = {
        "year": year,
        "total_tweets": total,
        "sentiment_counts": dict(sorted(sentiments.items())),
        "emotion_counts": dict(sorted(emotions.items())),
        "sarcasm_rate": 0.0 if total == 0 else round(sarcasm_count / total, 6),
        "low_confidence_count": low_confidence_count,
    }
    validate_summary(summary)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return out_path

