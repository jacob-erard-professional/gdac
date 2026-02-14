import argparse
import json
import re
from pathlib import Path

import pandas as pd

WHITESPACE_RE = re.compile(r"\s+")


def _strip_all_whitespace(value: str) -> str:
    return WHITESPACE_RE.sub("", str(value))


def count_name_matches(
    input_file: Path,
    *,
    names: list[str],
    text_column: str = "text",
    chunk_size: int = 100_000,
) -> dict:
    cleaned_names = [name.strip() for name in names if name.strip()]
    if not cleaned_names:
        raise ValueError("At least one non-empty name is required.")

    canonical_to_variants: dict[str, list[str]] = {}
    for name in cleaned_names:
        canonical = _strip_all_whitespace(name).lower()
        if not canonical:
            continue
        canonical_to_variants.setdefault(canonical, [])
        if name not in canonical_to_variants[canonical]:
            canonical_to_variants[canonical].append(name)

    canonical_names = sorted(canonical_to_variants.keys())
    counts = {name: 0 for name in canonical_names}
    total_rows = 0

    for chunk in pd.read_csv(input_file, dtype=str, keep_default_na=False, chunksize=chunk_size):
        if text_column not in chunk.columns:
            raise ValueError(f"Input file missing required column: {text_column}")
        text = chunk[text_column].astype(str).map(_strip_all_whitespace).str.lower()
        total_rows += len(chunk)
        for canonical in canonical_names:
            counts[canonical] += int(text.str.contains(canonical, regex=False).sum())

    return {
        "total_rows": int(total_rows),
        "names": [
            {
                "name": canonical,
                "matching_rows": int(counts[canonical]),
                "input_variants": canonical_to_variants[canonical],
            }
            for canonical in canonical_names
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Count rows whose text contains any of the provided names."
    )
    parser.add_argument("--year", type=str, help="Year under data/raw/<year>/")
    parser.add_argument("--input-file", type=Path, help="Explicit input CSV path")
    parser.add_argument(
        "--names",
        type=str,
        help='Comma-separated names (example: "beyonce,taylor swift,nike")',
    )
    parser.add_argument(
        "--names-file",
        type=Path,
        help="Path to a .txt file with one name per line",
    )
    parser.add_argument("--text-column", type=str, default="text")
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
        output_file = base_dir / "outputs" / "analytics" / year / "name_match_counts.json"

    if not args.names and not args.names_file:
        raise ValueError("Provide one of --names or --names-file")
    if args.names and args.names_file:
        raise ValueError("Provide only one of --names or --names-file")

    if args.names_file:
        if not args.names_file.exists():
            raise FileNotFoundError(f"Names file not found: {args.names_file}")
        names = [
            line.strip()
            for line in args.names_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    else:
        names = [part.strip() for part in args.names.split(",") if part.strip()]
    result = count_name_matches(
        input_file,
        names=names,
        text_column=args.text_column,
        chunk_size=args.chunk_size,
    )
    result["input_file"] = str(input_file)
    result["year"] = year
    result["text_column"] = args.text_column

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
