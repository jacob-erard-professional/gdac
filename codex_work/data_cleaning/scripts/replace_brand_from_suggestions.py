import argparse
import csv
from pathlib import Path


def is_false(value: str) -> bool:
    return (value or "").strip().lower() in {"false", "0", "no", "n", "f"}


def first_non_empty(row: dict[str, str], fieldnames: list[str]) -> str:
    for name in fieldnames:
        value = (row.get(name) or "").strip()
        if value:
            return value
    return ""


def load_brand_list(path: Path) -> dict[str, str]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["brand"]:
            raise SystemExit("Brand list CSV must contain exactly one header named 'brand'")

        brands: dict[str, str] = {}
        for row in reader:
            brand = (row.get("brand") or "").strip()
            if not brand:
                raise SystemExit("Brand list CSV contains a blank brand value")
            brands[brand.lower()] = brand

    if not brands:
        raise SystemExit("Brand list CSV must contain at least one brand")
    return brands


def replace_brand_values(
    input_path: Path,
    output_path: Path,
    allowed_brands: dict[str, str],
) -> tuple[int, int, int]:
    updated = 0
    skipped_empty = 0
    skipped_not_in_list = 0

    with input_path.open("r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames or []

        required = {"brand", "suggested_brand", "is_about_brand"}
        missing = sorted(name for name in required if name not in fieldnames)
        if missing:
            raise SystemExit(f"Missing required columns: {', '.join(missing)}")

        # Accept both spellings for assigned brand.
        assigned_candidates = [name for name in ["assgined_brand", "assigned_brand"] if name in fieldnames]

        with output_path.open("w", newline="", encoding="utf-8") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                if is_false(row.get("is_about_brand", "")):
                    replacement = first_non_empty(
                        row,
                        ["suggested_brand", *assigned_candidates],
                    )
                    if replacement:
                        canonical_brand = allowed_brands.get(replacement.lower())
                        if canonical_brand:
                            row["brand"] = canonical_brand
                            row["is_about_brand"] = "true"
                            updated += 1
                        else:
                            skipped_not_in_list += 1
                    else:
                        skipped_empty += 1

                writer.writerow(row)

    return updated, skipped_empty, skipped_not_in_list


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Replace brand with suggested_brand for rows where is_about_brand is false. "
            "If suggested_brand is empty, fall back to assgined_brand/assigned_brand."
        )
    )
    parser.add_argument("--input", required=True, help="Path to input CSV")
    parser.add_argument("--output", required=True, help="Path to output CSV")
    parser.add_argument(
        "--brand-list",
        required=True,
        help="Path to CSV with exactly one 'brand' column of allowed brands",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    brand_list_path = Path(args.brand_list)

    if not input_path.exists():
        raise SystemExit(f"Input CSV not found: {input_path}")
    if not brand_list_path.exists():
        raise SystemExit(f"Brand list CSV not found: {brand_list_path}")

    allowed_brands = load_brand_list(brand_list_path)
    updated, skipped_empty, skipped_not_in_list = replace_brand_values(
        input_path,
        output_path,
        allowed_brands,
    )
    print(
        "Updated "
        f"{updated} rows; skipped {skipped_empty} rows with no replacement value; "
        f"skipped {skipped_not_in_list} rows with replacement not in brand list."
    )
    print(f"Wrote output to {output_path}")


if __name__ == "__main__":
    main()
