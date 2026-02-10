import argparse
import json
import re
from pathlib import Path

import pandas as pd


SPLIT_RE = re.compile(r"[|,;/]+")


def _parse_brands(value: str) -> list[str]:
    if value is None:
        return []
    text = str(value).strip()
    if not text:
        return []
    if text.startswith("[") and text.endswith("]"):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except json.JSONDecodeError:
            pass
    parts = [p.strip() for p in SPLIT_RE.split(text) if p.strip()]
    return parts


def collect_unique_brands(input_file: Path, *, chunk_size: int = 100_000) -> list[str]:
    unique: set[str] = set()
    for chunk in pd.read_csv(input_file, dtype=str, keep_default_na=False, chunksize=chunk_size):
        column = "brands" if "brands" in chunk.columns else ("brand" if "brand" in chunk.columns else None)
        if column is None:
            raise ValueError("Input file missing required column: brands or brand")
        for value in chunk[column].tolist():
            for brand in _parse_brands(value):
                unique.add(brand.lower())
    return sorted(unique)


def main() -> None:
    parser = argparse.ArgumentParser(description="List unique brand names from tweets.csv.")
    parser.add_argument("--year", type=str, help="Year under data/raw/<year>/")
    parser.add_argument("--input-file", type=Path, help="Explicit input CSV path")
    parser.add_argument("--output-file", type=Path, help="Output JSON path")
    parser.add_argument("--chunk-size", type=int, default=100_000)
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
        output_file = base_dir / "outputs" / "analytics" / year / "unique_brand_names.json"

    brands = collect_unique_brands(input_file, chunk_size=args.chunk_size)
    payload = {
        "year": year,
        "unique_brands": brands,
        "unique_count": int(len(brands)),
    }
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
