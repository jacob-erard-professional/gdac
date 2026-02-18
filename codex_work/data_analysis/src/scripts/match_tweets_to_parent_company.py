"""Utility script for match tweets to parent company operations."""

import argparse
from pathlib import Path

from src.utils.tweet_company_map import build_parent_company_tweet_map_jsonl


def main():
    parser = argparse.ArgumentParser(description="Match tweets to parent companies in batches.")
    parser.add_argument("--enriched-file", required=True, type=Path, help="Path to enriched.csv")
    parser.add_argument("--brand-groups-file", required=True, type=Path, help="Path to brand_groups.json")
    parser.add_argument("--parent-groups-file", required=True, type=Path, help="Path to parent_company_groups.json")
    parser.add_argument("--output-file", required=True, type=Path, help="Output JSONL path")
    parser.add_argument("--year", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=1000)
    args = parser.parse_args()

    output_path = args.output_file
    if not output_path.is_absolute():
        output_path = (Path.cwd() / output_path).resolve()
    if "/outputs/analytics/" in str(output_path):
        parts = str(output_path).split("/outputs/analytics/")
        if len(parts) == 2:
            output_path = Path(parts[0]) / "outputs" / "aux" / parts[1]
            print(f"[tweet-map] redirecting output to aux: {output_path}")

    build_parent_company_tweet_map_jsonl(
        enriched_path=args.enriched_file,
        brand_groups_path=args.brand_groups_file,
        parent_company_groups_path=args.parent_groups_file,
        output_path=output_path,
        year=args.year,
        batch_size=args.batch_size,
    )


if __name__ == "__main__":
    main()
