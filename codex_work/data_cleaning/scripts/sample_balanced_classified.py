import argparse
import csv
import random
from pathlib import Path
from typing import Dict, List


def parse_is_about_brand(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def read_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"text", "brand", "is_about_brand"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")
        return list(reader)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sample 200 rows from classified_full.csv: 100 true + 100 false"
    )
    parser.add_argument(
        "--input",
        default="data/output/classified_full.csv",
        help="Input CSV path (default: data/output/classified_full.csv)",
    )
    parser.add_argument(
        "--output",
        default="data/output/classified_full_sample_200.csv",
        help="Output CSV path (default: data/output/classified_full_sample_200.csv)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible sampling (default: 42)",
    )
    args = parser.parse_args()

    random.seed(args.seed)
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    rows = read_rows(input_path)
    true_rows = [r for r in rows if parse_is_about_brand(r.get("is_about_brand", ""))]
    false_rows = [r for r in rows if not parse_is_about_brand(r.get("is_about_brand", ""))]

    if len(true_rows) < 100:
        raise SystemExit(f"Not enough true rows: found {len(true_rows)}, need 100")
    if len(false_rows) < 100:
        raise SystemExit(f"Not enough false rows: found {len(false_rows)}, need 100")

    sample_true = random.sample(true_rows, 100)
    sample_false = random.sample(false_rows, 100)
    sample = sample_true + sample_false
    random.shuffle(sample)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["text", "brand", "is_about_brand"])
        writer.writeheader()
        for row in sample:
            writer.writerow(
                {
                    "text": row.get("text", ""),
                    "brand": row.get("brand", ""),
                    "is_about_brand": row.get("is_about_brand", ""),
                }
            )

    print(f"Wrote 200 rows to {output_path}")


if __name__ == "__main__":
    main()
