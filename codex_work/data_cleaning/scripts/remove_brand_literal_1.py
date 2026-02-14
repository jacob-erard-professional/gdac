import argparse
import csv
from pathlib import Path


def clean_brand(value: str) -> str:
    return str(value).replace("_1", "")


def process_csv(input_path: Path, output_path: Path) -> int:
    updated = 0
    with input_path.open("r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames or []
        if "brand" not in fieldnames:
            raise ValueError("CSV must contain a 'brand' column")

        with output_path.open("w", newline="", encoding="utf-8") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in reader:
                original = row.get("brand", "")
                cleaned = clean_brand(original)
                if cleaned != original:
                    updated += 1
                row["brand"] = cleaned
                writer.writerow(row)
    return updated


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove literal '_1' from all values in the brand column."
    )
    parser.add_argument("--input", required=True, help="Target CSV path")
    parser.add_argument(
        "--output",
        default=None,
        help="Output CSV path (default: overwrite input)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    output_path = Path(args.output) if args.output else input_path

    if output_path == input_path:
        temp_path = input_path.with_suffix(input_path.suffix + ".tmp")
        updated = process_csv(input_path, temp_path)
        temp_path.replace(input_path)
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        updated = process_csv(input_path, output_path)

    print(f"Updated {updated} rows in {output_path}")


if __name__ == "__main__":
    main()
