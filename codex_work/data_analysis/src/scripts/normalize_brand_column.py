import argparse
import re
from pathlib import Path

import pandas as pd


SUFFIX_RE = re.compile(r"_\d+$")
SPACE_RE = re.compile(r"\s+")


def normalize_brand(
    value: object,
    *,
    strip_numeric_suffix: bool,
    lowercase: bool,
) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    text = SPACE_RE.sub(" ", text)
    if strip_numeric_suffix:
        text = SUFFIX_RE.sub("", text).strip()
    if lowercase:
        text = text.lower()
    return text


def run(
    *,
    input_csv: Path,
    output_csv: Path,
    brand_column: str,
    strip_numeric_suffix: bool,
    lowercase: bool,
    chunk_size: int,
    encoding: str,
) -> Path:
    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")
    if chunk_size < 1:
        raise ValueError("chunk_size must be >= 1")

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    inplace = input_csv.resolve() == output_csv.resolve()
    temp_output = output_csv.with_name(f"{output_csv.stem}.tmp{output_csv.suffix}") if inplace else output_csv
    if temp_output.exists():
        temp_output.unlink()

    first_chunk = True
    resolved_brand_column: str | None = None
    csv_iter = pd.read_csv(
        input_csv,
        dtype=str,
        keep_default_na=False,
        chunksize=chunk_size,
        encoding=encoding,
        encoding_errors="replace",
    )
    for chunk in csv_iter:
        if resolved_brand_column is None:
            if brand_column in chunk.columns:
                resolved_brand_column = brand_column
            else:
                lower_to_original = {str(col).lower(): str(col) for col in chunk.columns}
                resolved_brand_column = lower_to_original.get(brand_column.lower())
            if resolved_brand_column is None:
                raise ValueError(f"Required brand column missing: '{brand_column}'")

        chunk[resolved_brand_column] = [
            normalize_brand(v, strip_numeric_suffix=strip_numeric_suffix, lowercase=lowercase)
            for v in chunk[resolved_brand_column].tolist()
        ]
        chunk.to_csv(temp_output, mode="w" if first_chunk else "a", index=False, header=first_chunk)
        first_chunk = False

    if inplace:
        temp_output.replace(output_csv)
    return output_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize the brand column in a CSV.")
    parser.add_argument("--input-csv", required=True, type=Path, help="Path to source CSV")
    parser.add_argument("--output-csv", type=Path, help="Output CSV path")
    parser.add_argument("--in-place", action="store_true", help="Update input CSV directly")
    parser.add_argument("--brand-column", default="brand", help="Brand column name (default: brand)")
    parser.add_argument(
        "--keep-suffix",
        action="store_true",
        help="Do not strip trailing numeric suffix like _1",
    )
    parser.add_argument(
        "--keep-case",
        action="store_true",
        help="Do not lowercase brand values",
    )
    parser.add_argument("--chunk-size", type=int, default=100_000, help="CSV rows per chunk")
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="CSV encoding (example: utf-8, utf-8-sig, latin1)",
    )
    args = parser.parse_args()

    if args.in_place and args.output_csv is not None:
        raise ValueError("Use either --in-place or --output-csv, not both.")

    output_csv = args.input_csv if args.in_place else args.output_csv
    if output_csv is None:
        output_csv = args.input_csv.with_name(f"{args.input_csv.stem}_normalized{args.input_csv.suffix}")

    written = run(
        input_csv=args.input_csv,
        output_csv=output_csv,
        brand_column=args.brand_column,
        strip_numeric_suffix=not args.keep_suffix,
        lowercase=not args.keep_case,
        chunk_size=args.chunk_size,
        encoding=args.encoding,
    )
    print(written)


if __name__ == "__main__":
    main()
