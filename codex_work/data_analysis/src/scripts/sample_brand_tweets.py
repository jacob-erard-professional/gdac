"""Utility script for sample brand tweets operations."""

import argparse
import json
from pathlib import Path

import pandas as pd


def sample_brand_tweets(
    input_file: Path,
    *,
    samples_per_brand: int,
    seed: int,
) -> pd.DataFrame:
    frame = pd.read_csv(input_file, dtype=str, keep_default_na=False)
    column = "brand" if "brand" in frame.columns else ("brands" if "brands" in frame.columns else None)
    if column is None:
        raise ValueError("Input file missing required column: brand or brands")
    if "text" not in frame.columns:
        raise ValueError("Input file missing required column: text")

    frame = frame.copy()
    frame[column] = frame[column].astype(str).str.strip()
    frame = frame[frame[column] != ""]

    grouped = []
    for brand, group in frame.groupby(column, sort=True):
        if group.empty:
            continue
        n = min(samples_per_brand, len(group))
        grouped.append(group.sample(n=n, random_state=seed))
    if not grouped:
        return frame.head(0)
    return pd.concat(grouped, ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sample a fixed number of random tweets per brand from a yearly CSV."
    )
    parser.add_argument("--year", type=str, help="Year under data/raw/<year>/")
    parser.add_argument("--input-file", type=Path, help="Explicit input CSV path")
    parser.add_argument("--output-file", type=Path, help="Output CSV path")
    parser.add_argument("--samples-per-brand", type=int, required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parents[2]
    if bool(args.year) == bool(args.input_file):
        raise ValueError("Provide exactly one of --year or --input-file")

    input_file = args.input_file
    year = args.year
    if input_file is None:
        input_file = base_dir / "data" / "raw" / year / "tweets.csv"
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    output_file = args.output_file
    if output_file is None:
        if year is None:
            raise ValueError("Provide --output-file when using --input-file")
        output_file = base_dir / "outputs" / "analytics" / year / "sampled_brand_tweets.csv"

    sampled = sample_brand_tweets(
        input_file,
        samples_per_brand=args.samples_per_brand,
        seed=args.seed,
    )
    output_file.parent.mkdir(parents=True, exist_ok=True)
    sampled.to_csv(output_file, index=False)

    stats = {
        "year": year,
        "input_file": str(input_file),
        "output_file": str(output_file),
        "samples_per_brand": int(args.samples_per_brand),
        "brands": int(sampled["brand"].nunique() if "brand" in sampled.columns else sampled["brands"].nunique()),
        "total_rows": int(len(sampled)),
    }
    stats_path = output_file.with_suffix(".json")
    stats_path.write_text(json.dumps(stats, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
