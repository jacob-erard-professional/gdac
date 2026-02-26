import argparse
import csv
from pathlib import Path
from typing import Dict, List, Tuple


METRIC_COLUMNS = (
    "public_metrics.retweet_count",
    "public_metrics.reply_count",
    "public_metrics.like_count",
    "public_metrics.quote_count",
    "public_metrics.bookmark_count",
    "public_metrics.impression_count",
)


def _as_int(value: str) -> int:
    try:
        return int(float((value or "").strip() or 0))
    except ValueError:
        return 0


def _metric_sum(row: Dict[str, str]) -> int:
    return sum(_as_int(row.get(column, "0")) for column in METRIC_COLUMNS)


def dedupe_rows(input_path: Path, output_path: Path) -> int:
    with input_path.open("r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames or []
        if "text" not in fieldnames:
            raise ValueError("Missing required column: text")

        best_by_text: Dict[str, Tuple[int, Dict[str, str]]] = {}
        text_order: List[str] = []

        for row in reader:
            text = (row.get("text") or "").strip()
            if text not in best_by_text:
                best_by_text[text] = (_metric_sum(row), row)
                text_order.append(text)
                continue

            current_sum, _ = best_by_text[text]
            candidate_sum = _metric_sum(row)
            if candidate_sum > current_sum:
                best_by_text[text] = (candidate_sum, row)

    with output_path.open("w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        for text in text_order:
            writer.writerow(best_by_text[text][1])

    return len(text_order)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Remove duplicate tweets by text, keeping the row with the highest "
            "sum of public metrics."
        )
    )
    parser.add_argument("--input", required=True, help="Input CSV path")
    parser.add_argument("--output", required=True, help="Output CSV path")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    kept = dedupe_rows(input_path, output_path)
    print(f"Kept {kept} rows in {output_path}")


if __name__ == "__main__":
    main()
