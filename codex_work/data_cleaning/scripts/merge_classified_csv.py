import argparse
import csv
from pathlib import Path


def merged_fieldnames(first_fields, second_fields):
    first_fields = first_fields or []
    second_fields = second_fields or []
    combined = list(first_fields)
    for field in second_fields:
        if field not in combined:
            combined.append(field)
    return combined


def read_rows(path: Path):
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames, list(reader)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge two classified CSV files into a single CSV."
    )
    parser.add_argument("--first", required=True, help="Path to first CSV (existing partial output)")
    parser.add_argument("--second", required=True, help="Path to second CSV (resume output)")
    parser.add_argument("--output", required=True, help="Path to merged CSV")
    args = parser.parse_args()

    first_path = Path(args.first)
    second_path = Path(args.second)
    output_path = Path(args.output)

    if not first_path.exists():
        raise SystemExit(f"First CSV not found: {first_path}")
    if not second_path.exists():
        raise SystemExit(f"Second CSV not found: {second_path}")

    first_fields, first_rows = read_rows(first_path)
    second_fields, second_rows = read_rows(second_path)

    fieldnames = merged_fieldnames(first_fields, second_fields)
    if not fieldnames:
        raise SystemExit("No CSV headers found in inputs.")

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in first_rows:
            writer.writerow(row)
        for row in second_rows:
            writer.writerow(row)

    total_rows = len(first_rows) + len(second_rows)
    print(
        f"Merged {len(first_rows)} + {len(second_rows)} rows into {output_path} ({total_rows} total rows)"
    )


if __name__ == "__main__":
    main()
