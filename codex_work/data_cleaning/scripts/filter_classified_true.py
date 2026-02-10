import argparse
import csv
from pathlib import Path


FALSE_VALUES = {"false", "0", "no", "n", ""}


def is_true(value: str) -> bool:
    return str(value).strip().lower() not in FALSE_VALUES


def filter_rows(input_path: Path, output_path: Path) -> int:
    kept = 0
    with input_path.open("r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames or []
        with output_path.open("w", newline="", encoding="utf-8") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in reader:
                if is_true(row.get("is_about_brand", "")):
                    writer.writerow(row)
                    kept += 1
    return kept


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove rows where is_about_brand is false."
    )
    parser.add_argument(
        "--input",
        default="data/output/classified.csv",
        help="Input CSV path (default: data/output/classified.csv)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output CSV path (default: overwrite input file)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path

    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    if output_path == input_path:
        temp_path = input_path.with_suffix(input_path.suffix + ".tmp")
        kept = filter_rows(input_path, temp_path)
        temp_path.replace(input_path)
    else:
        kept = filter_rows(input_path, output_path)

    print(f"Kept {kept} rows in {output_path}")


if __name__ == "__main__":
    main()
