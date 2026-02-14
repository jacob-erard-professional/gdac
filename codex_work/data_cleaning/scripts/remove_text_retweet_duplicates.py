import argparse
import csv
from pathlib import Path


TEXT_COLUMN = "text"
RETWEET_COLUMNS = ("public_metrics.retweet_count", "retweet_count")


def _resolve_retweet_column(fieldnames: list[str]) -> str:
    for column in RETWEET_COLUMNS:
        if column in fieldnames:
            return column
    raise ValueError(
        "Missing retweet count column. Expected one of: "
        + ", ".join(RETWEET_COLUMNS)
    )


def dedupe_by_text_and_retweets(input_path: Path, output_path: Path) -> int:
    seen_keys: set[tuple[str, str]] = set()
    kept = 0

    with input_path.open("r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames or []
        if TEXT_COLUMN not in fieldnames:
            raise ValueError(f"Missing required column: {TEXT_COLUMN}")
        retweet_column = _resolve_retweet_column(fieldnames)

        with output_path.open("w", newline="", encoding="utf-8") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                key = (
                    (row.get(TEXT_COLUMN) or "").strip(),
                    (row.get(retweet_column) or "").strip(),
                )
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                writer.writerow(row)
                kept += 1

    return kept


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Remove duplicate rows where both text and retweet count match. "
            "Keeps first occurrence."
        )
    )
    parser.add_argument("--input", required=True, help="Input CSV path")
    parser.add_argument(
        "--output",
        default=None,
        help="Output CSV path (default: overwrite input in place)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    output_path = Path(args.output) if args.output else input_path
    if output_path == input_path:
        temp_path = input_path.with_suffix(input_path.suffix + ".tmp")
        kept = dedupe_by_text_and_retweets(input_path, temp_path)
        temp_path.replace(input_path)
    else:
        kept = dedupe_by_text_and_retweets(input_path, output_path)

    print(f"Kept {kept} rows in {output_path}")


if __name__ == "__main__":
    main()
