"""Utility script for reclassify sentiment by confidence operations."""

import argparse
import json
from pathlib import Path


def _reclassify(records: list[dict], threshold: float, label_field: str) -> list[dict]:
    updated = []
    for record in records:
        confidence = record.get("confidence")
        try:
            conf_value = float(confidence)
        except (TypeError, ValueError):
            conf_value = None
        if conf_value is not None and conf_value < threshold:
            record = dict(record)
            record[label_field] = "neutral"
        updated.append(record)
    return updated


def main():
    parser = argparse.ArgumentParser(description="Reclassify sentiment.json by confidence threshold.")
    parser.add_argument("--input-file", required=True, type=Path, help="Input sentiment.json path")
    parser.add_argument("--output-file", required=True, type=Path, help="Output sentiment.json path")
    parser.add_argument("--threshold", type=float, default=0.65)
    parser.add_argument(
        "--label-field",
        default="sentiment",
        help="Field to reclassify (sentiment or main_sentiment)",
    )
    args = parser.parse_args()

    payload = json.loads(args.input_file.read_text(encoding="utf-8"))
    records = payload.get("records", [])
    payload["records"] = _reclassify(records, args.threshold, args.label_field)
    payload.setdefault("metadata", {})
    payload["metadata"]["reclassify_threshold"] = args.threshold
    payload["metadata"]["reclassify_rule"] = "confidence<threshold -> neutral"
    payload["metadata"]["reclassify_label_field"] = args.label_field

    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    args.output_file.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
