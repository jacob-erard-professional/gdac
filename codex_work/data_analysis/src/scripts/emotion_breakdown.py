import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def _load_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            records.extend(payload.get("records", []))
    return records


def _breakdown(records: list[dict], key: str) -> list[dict]:
    grouped: dict[str, Counter] = defaultdict(Counter)
    for record in records:
        company = str(record.get(key, "")).strip() or "unmatched"
        emotion = str(record.get("sentiment_label", "")).strip().lower()
        if not emotion:
            continue
        grouped[company][emotion] += 1

    output: list[dict] = []
    for company, counts in grouped.items():
        total = sum(counts.values())
        if total <= 0:
            continue
        breakdown = {emotion: round(count / total, 6) for emotion, count in sorted(counts.items())}
        output.append(
            {
                "parent_company" if key == "primary_parent_company" else "brand": company,
                "sentiment_breakdown": breakdown,
                "tweet_count": total,
            }
        )

    output.sort(key=lambda item: (-int(item["tweet_count"]), str(item.get("parent_company") or item.get("brand"))))
    return output


def main():
    parser = argparse.ArgumentParser(description="Compute emotion breakdowns per parent company and brand.")
    parser.add_argument("--input-jsonl", required=True, type=Path, help="JSONL from match_sentiment_to_companies")
    parser.add_argument("--parent-out", required=True, type=Path, help="Output JSON for parent companies")
    parser.add_argument("--brand-out", required=True, type=Path, help="Output JSON for brands")
    args = parser.parse_args()

    input_path = args.input_jsonl
    if not input_path.is_absolute():
        input_path = (Path.cwd() / input_path).resolve()
    if "/outputs/analytics/" in str(input_path):
        parts = str(input_path).split("/outputs/analytics/")
        if len(parts) == 2:
            input_path = Path(parts[0]) / "outputs" / "aux" / parts[1]
            print(f"[emotion-breakdown] redirecting input to aux: {input_path}")

    parent_out = args.parent_out
    if not parent_out.is_absolute():
        parent_out = (Path.cwd() / parent_out).resolve()
    if "/outputs/analytics/" in str(parent_out):
        parts = str(parent_out).split("/outputs/analytics/")
        if len(parts) == 2:
            parent_out = Path(parts[0]) / "outputs" / "aux" / parts[1]
            print(f"[emotion-breakdown] redirecting parent output to aux: {parent_out}")

    brand_out = args.brand_out
    if not brand_out.is_absolute():
        brand_out = (Path.cwd() / brand_out).resolve()
    if "/outputs/analytics/" in str(brand_out):
        parts = str(brand_out).split("/outputs/analytics/")
        if len(parts) == 2:
            brand_out = Path(parts[0]) / "outputs" / "aux" / parts[1]
            print(f"[emotion-breakdown] redirecting brand output to aux: {brand_out}")

    records = _load_jsonl(input_path)

    parent_rows = _breakdown(records, "primary_parent_company")
    brand_rows = _breakdown(records, "primary_brand")

    parent_out.parent.mkdir(parents=True, exist_ok=True)
    brand_out.parent.mkdir(parents=True, exist_ok=True)

    parent_out.write_text(json.dumps(parent_rows, indent=2, sort_keys=True), encoding="utf-8")
    brand_out.write_text(json.dumps(brand_rows, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
