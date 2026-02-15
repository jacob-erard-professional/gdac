import argparse
import json
from pathlib import Path

import pandas as pd


def _normalize(value: object, *, case_sensitive: bool) -> str:
    text = str(value or "").strip()
    return text if case_sensitive else text.lower()


def _load_brand_to_industry(
    mapping_json: Path,
    *,
    case_sensitive: bool,
    duplicate_policy: str,
) -> dict[str, str]:
    payload = json.loads(mapping_json.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Mapping JSON must be an object: {industry: [brand, ...], ...}")

    brand_to_industry: dict[str, str] = {}
    for industry, brands in payload.items():
        if not isinstance(brands, list):
            raise ValueError(f"Industry '{industry}' must map to a list of brands.")
        for brand in brands:
            key = _normalize(brand, case_sensitive=case_sensitive)
            if not key:
                continue

            if key in brand_to_industry and brand_to_industry[key] != industry:
                if duplicate_policy == "error":
                    raise ValueError(
                        f"Brand '{brand}' appears in multiple industries: "
                        f"'{brand_to_industry[key]}' and '{industry}'."
                    )
                if duplicate_policy == "first":
                    continue
                if duplicate_policy == "last":
                    brand_to_industry[key] = str(industry)
                    continue

            brand_to_industry[key] = str(industry)
    return brand_to_industry


def run(
    *,
    input_csv: Path,
    mapping_json: Path,
    output_csv: Path,
    brand_column: str,
    industry_column: str,
    default_industry: str,
    case_sensitive: bool,
    duplicate_policy: str,
    chunk_size: int,
    encoding: str,
) -> Path:
    if chunk_size < 1:
        raise ValueError("chunk_size must be >= 1")
    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")
    if not mapping_json.exists():
        raise FileNotFoundError(f"Mapping JSON not found: {mapping_json}")

    brand_to_industry = _load_brand_to_industry(
        mapping_json,
        case_sensitive=case_sensitive,
        duplicate_policy=duplicate_policy,
    )

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    inplace = input_csv.resolve() == output_csv.resolve()
    temp_output_csv = (
        output_csv.with_name(f"{output_csv.stem}.tmp{output_csv.suffix}") if inplace else output_csv
    )
    if temp_output_csv.exists():
        temp_output_csv.unlink()

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

        chunk[industry_column] = [
            brand_to_industry.get(_normalize(brand, case_sensitive=case_sensitive), default_industry)
            for brand in chunk[resolved_brand_column].tolist()
        ]

        chunk.to_csv(
            temp_output_csv,
            mode="w" if first_chunk else "a",
            index=False,
            header=first_chunk,
        )
        first_chunk = False

    if inplace:
        temp_output_csv.replace(output_csv)

    return output_csv


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Add an industry column to a CSV by matching values in the brand column "
            "against a JSON map of {industry: [brand, ...]}."
        )
    )
    parser.add_argument("--input-csv", required=True, type=Path, help="Path to source CSV")
    parser.add_argument("--mapping-json", required=True, type=Path, help="Path to mapping JSON")
    parser.add_argument("--output-csv", type=Path, help="Output CSV path")
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Update the input CSV directly (append/overwrite the industry column in same file)",
    )
    parser.add_argument("--brand-column", default="brand", help="Brand column name in input CSV")
    parser.add_argument("--industry-column", default="industry", help="Industry column name to add")
    parser.add_argument(
        "--default-industry",
        default="unmapped",
        help="Fallback value when a brand is not found in mapping",
    )
    parser.add_argument(
        "--case-sensitive",
        action="store_true",
        help="Use case-sensitive brand matching (default: case-insensitive)",
    )
    parser.add_argument(
        "--duplicate-policy",
        choices=["error", "first", "last"],
        default="error",
        help="How to handle brands listed under multiple industries in mapping JSON",
    )
    parser.add_argument("--chunk-size", type=int, default=100_000, help="CSV rows per processing chunk")
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="CSV file encoding (example: utf-8, utf-8-sig, latin1)",
    )
    args = parser.parse_args()

    if args.in_place and args.output_csv is not None:
        raise ValueError("Use either --in-place or --output-csv, not both.")

    output_csv = args.output_csv
    if args.in_place:
        output_csv = args.input_csv
    elif output_csv is None:
        output_csv = args.input_csv.with_name(f"{args.input_csv.stem}_with_industry.csv")

    written = run(
        input_csv=args.input_csv,
        mapping_json=args.mapping_json,
        output_csv=output_csv,
        brand_column=args.brand_column,
        industry_column=args.industry_column,
        default_industry=args.default_industry,
        case_sensitive=args.case_sensitive,
        duplicate_policy=args.duplicate_policy,
        chunk_size=args.chunk_size,
        encoding=args.encoding,
    )
    print(written)


if __name__ == "__main__":
    main()
