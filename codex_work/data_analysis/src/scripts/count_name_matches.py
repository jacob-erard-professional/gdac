import argparse
import json
import re
from pathlib import Path

import pandas as pd

WHITESPACE_RE = re.compile(r"\s+")


def _strip_all_whitespace(value: str) -> str:
    return WHITESPACE_RE.sub("", str(value))


def _build_name_maps(names: list[str]) -> tuple[list[str], dict[str, list[str]]]:
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
    if not canonical_names:
        raise ValueError("At least one non-empty name is required.")
    return canonical_names, canonical_to_variants


def count_name_matches(
    input_file: Path,
    *,
    names: list[str],
    text_column: str = "text",
    chunk_size: int = 100_000,
) -> dict:
    canonical_names, canonical_to_variants = _build_name_maps(names)
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
        "names": sorted(
            [
                {
                    "name": canonical,
                    "matching_rows": int(counts[canonical]),
                    "input_variants": canonical_to_variants[canonical],
                }
                for canonical in canonical_names
            ],
            key=lambda item: (-int(item["matching_rows"]), str(item["name"])),
        ),
    }


def write_rows_with_any_name(
    input_file: Path,
    *,
    names: list[str],
    output_file: Path,
    text_column: str = "text",
    chunk_size: int = 100_000,
) -> int:
    canonical_names, _canonical_to_variants = _build_name_maps(names)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    if output_file.exists():
        output_file.unlink()

    matched_rows = 0
    first_chunk = True
    for chunk in pd.read_csv(input_file, dtype=str, keep_default_na=False, chunksize=chunk_size):
        if text_column not in chunk.columns:
            raise ValueError(f"Input file missing required column: {text_column}")
        normalized_text = chunk[text_column].astype(str).map(_strip_all_whitespace).str.lower()
        mask = pd.Series(False, index=chunk.index)
        for canonical in canonical_names:
            mask = mask | normalized_text.str.contains(canonical, regex=False)

        matched = chunk.loc[mask]
        if matched.empty:
            continue
        matched_rows += int(len(matched))
        matched.to_csv(
            output_file,
            mode="w" if first_chunk else "a",
            index=False,
            header=first_chunk,
        )
        first_chunk = False

    return matched_rows


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
    parser.add_argument(
        "--matched-rows-output-file",
        type=Path,
        help="Optional output CSV path containing only rows whose text matches any provided name",
    )
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

    if args.matched_rows_output_file:
        matched_output = args.matched_rows_output_file
        if not matched_output.is_absolute():
            matched_output = (base_dir / matched_output).resolve()
        matched_rows = write_rows_with_any_name(
            input_file,
            names=names,
            output_file=matched_output,
            text_column=args.text_column,
            chunk_size=args.chunk_size,
        )
        result["matched_rows_output_file"] = str(matched_output)
        result["matched_rows_written"] = int(matched_rows)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
