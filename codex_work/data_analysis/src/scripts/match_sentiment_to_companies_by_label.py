import argparse
import json
import re
from pathlib import Path

from src.utils.tweet_company_map import _load_brand_groups, _load_parent_company_groups

HASHTAG_RE = re.compile(r"#(\w+)")


def _extract_hashtags(text: str) -> list[str]:
    hashtags = [tag.lower() for tag in HASHTAG_RE.findall(text or "") if tag]
    return list(dict.fromkeys(hashtags))


def _select_primary(items: list[str]) -> str:
    return items[0] if items else "unmatched"


def _redirect_aux(path: Path, *, label: str) -> Path:
    resolved = path if path.is_absolute() else (Path.cwd() / path).resolve()
    if "/outputs/analytics/" in str(resolved):
        parts = str(resolved).split("/outputs/analytics/")
        if len(parts) == 2:
            redirected = Path(parts[0]) / "outputs" / "aux" / parts[1]
            print(f"[sentiment-map] redirecting {label} to aux: {redirected}")
            return redirected
    return resolved


def main():
    parser = argparse.ArgumentParser(
        description="Match sentiment records to brand and parent company groups using a chosen label field."
    )
    parser.add_argument("--sentiment-file", required=True, type=Path, help="Path to sentiment.json")
    parser.add_argument("--brand-groups-file", required=True, type=Path, help="Path to brand_groups.json")
    parser.add_argument("--parent-groups-file", required=True, type=Path, help="Path to parent_company_groups.json")
    parser.add_argument("--output-file", required=True, type=Path, help="Output JSONL path")
    parser.add_argument("--label-field", default="sentiment", help="Label field to include (default: sentiment)")
    parser.add_argument("--batch-size", type=int, default=1000)
    args = parser.parse_args()

    if args.batch_size < 1:
        raise ValueError("batch_size must be >= 1")

    payload = json.loads(args.sentiment_file.read_text(encoding="utf-8"))
    records = payload.get("records", [])

    output_path = _redirect_aux(args.output_file, label="output")
    hashtag_to_brand, _hashtag_counts = _load_brand_groups(args.brand_groups_file)
    parent_map = _load_parent_company_groups(args.parent_groups_file)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    total = len(records)
    with output_path.open("w", encoding="utf-8") as f:
        for start in range(0, total, args.batch_size):
            batch = records[start : start + args.batch_size]
            out_records = []
            for record in batch:
                text = str(record.get("text", ""))
                hashtags = _extract_hashtags(text)
                brand_tags = []
                for tag in hashtags:
                    brand = hashtag_to_brand.get(tag)
                    if brand:
                        brand_tags.append(brand)
                brand_tags = sorted(set(brand_tags))
                primary_brand = _select_primary(brand_tags)
                parent_tags = sorted({parent_map.get(brand) for brand in brand_tags if parent_map.get(brand)})
                primary_parent = parent_map.get(primary_brand) or _select_primary(parent_tags)

                out = {
                    "tweet_id": str(record.get("tweet_id", "")).strip(),
                    "pipeline_row_id": str(record.get("pipeline_row_id", "")).strip(),
                    "year": record.get("year"),
                    "hashtags": hashtags,
                    "brand_tags": brand_tags,
                    "primary_brand": primary_brand,
                    "parent_company_tags": parent_tags,
                    "primary_parent_company": primary_parent or "unmatched",
                    "sentiment_label": record.get(args.label_field),
                    "confidence": record.get("confidence"),
                }
                out_records.append(out)

            f.write(
                json.dumps(
                    {
                        "batch_start": int(start),
                        "batch_size": int(len(batch)),
                        "records": out_records,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            print(
                f"[sentiment-map] wrote batch {start // args.batch_size + 1} "
                f"rows={len(batch)} total={total}"
            )


if __name__ == "__main__":
    main()
