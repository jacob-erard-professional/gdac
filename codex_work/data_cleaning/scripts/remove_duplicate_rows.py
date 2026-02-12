import argparse
import csv
from pathlib import Path
from typing import Iterable


def dedupe_rows(input_path: Path, output_path: Path) -> int:
    seen = set()
    kept = 0

    with input_path.open("r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames or []

        with output_path.open("w", newline="", encoding="utf-8") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                key = tuple((name, row.get(name, "")) for name in fieldnames)
                if key in seen:
                    continue
                seen.add(key)
                writer.writerow(row)
                kept += 1

    return kept


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove duplicate rows from a CSV (keeps first occurrence)."
    )
    parser.add_argument(
        "--input",
        required=True,
        nargs=2,
        metavar=("YEAR", "FILE_NAME"),
        help="Input selector as: YEAR FILE_NAME (resolved to data/output/raw/<YEAR>/<FILE_NAME>)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file name in the same year directory (default: overwrite input file)",
    )
    args = parser.parse_args()

    year, file_name = args.input
    base_dir = Path("data/output/raw") / year
    input_path = base_dir / file_name
    output_path = (base_dir / args.output) if args.output else input_path

    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    if output_path == input_path:
        temp_path = input_path.with_suffix(input_path.suffix + ".tmp")
        kept = dedupe_rows(input_path, temp_path)
        temp_path.replace(input_path)
    else:
        kept = dedupe_rows(input_path, output_path)

    print(f"Kept {kept} unique rows in {output_path}")


if __name__ == "__main__":
    main()
