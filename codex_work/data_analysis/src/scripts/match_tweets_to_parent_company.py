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

    build_parent_company_tweet_map_jsonl(
        enriched_path=args.enriched_file,
        brand_groups_path=args.brand_groups_file,
        parent_company_groups_path=args.parent_groups_file,
        output_path=args.output_file,
        year=args.year,
        batch_size=args.batch_size,
    )


if __name__ == "__main__":
    main()
