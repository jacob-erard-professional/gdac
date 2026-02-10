import argparse
import csv
import json
from typing import Dict, Iterable


def read_csv(path: str) -> Iterable[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield row


def read_jsonl(path: str) -> Iterable[Dict[str, str]]:
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def write_csv(path: str, rows: Iterable[Dict[str, str]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["brand", "text", "is_about_brand"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def extract_rows(rows: Iterable[Dict[str, str]]) -> Iterable[Dict[str, str]]:
    for row in rows:
        yield {
            "brand": row.get("brand", ""),
            "text": row.get("text", ""),
            "is_about_brand": row.get("is_about_brand", ""),
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract brand, text, and is_about_brand columns.")
    parser.add_argument("--input", required=True, help="Path to input CSV or JSONL")
    parser.add_argument("--output", required=True, help="Path to output CSV")
    parser.add_argument("--format", choices=["csv", "jsonl"], default="csv")
    args = parser.parse_args()

    if args.format == "jsonl":
        rows = read_jsonl(args.input)
    else:
        rows = read_csv(args.input)

    write_csv(args.output, extract_rows(rows))


if __name__ == "__main__":
    main()
