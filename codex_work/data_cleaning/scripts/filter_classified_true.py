import argparse
import csv
from pathlib import Path


FALSE_VALUES = {"false", "0", "no", "n", ""}
READ_ENCODINGS = ("utf-8", "utf-8-sig", "cp1252", "latin-1")


def is_true(value: str) -> bool:
    return str(value).strip().lower() not in FALSE_VALUES


def filter_rows_with_encoding(input_path: Path, output_path: Path, encoding: str) -> int:
    kept = 0
    with input_path.open("r", newline="", encoding=encoding) as infile:
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


def filter_rows(input_path: Path, output_path: Path) -> tuple[int, str]:
    last_error: UnicodeDecodeError | None = None
    for encoding in READ_ENCODINGS:
        try:
            kept = filter_rows_with_encoding(input_path, output_path, encoding)
            return kept, encoding
        except UnicodeDecodeError as exc:
            last_error = exc

    if last_error is not None:
        raise SystemExit(
            "Could not decode input CSV with supported encodings: "
            + ", ".join(READ_ENCODINGS)
        ) from last_error
    raise SystemExit("Failed to process CSV for an unknown reason.")


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
        kept, encoding = filter_rows(input_path, temp_path)
        temp_path.replace(input_path)
    else:
        kept, encoding = filter_rows(input_path, output_path)

    print(f"Kept {kept} rows in {output_path}")
    print(f"Read input using encoding: {encoding}")


if __name__ == "__main__":
    main()
