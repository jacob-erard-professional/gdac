"""Utility script for top words frequency operations."""

import argparse
import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd

WORD_RE = re.compile(r"[A-Za-z0-9']+")


def compute_top_words(input_file: Path, *, text_column: str, top_n: int, chunk_size: int) -> dict:
    """Count word frequencies from a CSV text column and return top-N words."""
    if top_n < 1:
        raise ValueError("top_n must be >= 1")
    if chunk_size < 1:
        raise ValueError("chunk_size must be >= 1")

    counts: Counter[str] = Counter()
    total_rows = 0
    total_tokens = 0

    for chunk in pd.read_csv(input_file, dtype=str, keep_default_na=False, chunksize=chunk_size):
        if text_column not in chunk.columns:
            raise ValueError(f"Input file missing required column: {text_column}")
        total_rows += len(chunk)
        for text in chunk[text_column].astype(str).tolist():
            tokens = [token.lower() for token in WORD_RE.findall(text)]
            total_tokens += len(tokens)
            counts.update(tokens)

    top_words = [
        {"word": word, "count": count}
        for word, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:top_n]
    ]

    return {
        "source_file": str(input_file),
        "text_column": text_column,
        "total_rows": int(total_rows),
        "total_tokens": int(total_tokens),
        "unique_words": int(len(counts)),
        "top_words": top_words,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract the most common words from a specified dataset CSV."
    )
    parser.add_argument("--year", type=str, help="Year under data/raw/<year>/")
    parser.add_argument("--input-file", type=Path, help="Explicit input CSV path")
    parser.add_argument("--output-file", type=Path, help="Output JSON path")
    parser.add_argument("--text-column", type=str, default="text", help="Column containing text")
    parser.add_argument("--top-n", type=int, default=50, help="Number of most common words to return")
    parser.add_argument("--chunk-size", type=int, default=100_000, help="CSV rows per chunk")
    args = parser.parse_args()

    if bool(args.year) == bool(args.input_file):
        raise ValueError("Provide exactly one of --year or --input-file")

    base_dir = Path(__file__).resolve().parents[2]
    input_file = args.input_file
    year = args.year
    if input_file is None:
        input_file = base_dir / "data" / "raw" / year / "tweets.csv"
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    output_file = args.output_file
    if output_file is None:
        if year is None:
            raise ValueError("Provide --output-file when using --input-file")
        output_file = base_dir / "outputs" / "analytics" / year / f"top_{args.top_n}_words.json"
    elif not output_file.is_absolute():
        output_file = (base_dir / output_file).resolve()

    result = compute_top_words(
        input_file,
        text_column=args.text_column,
        top_n=args.top_n,
        chunk_size=args.chunk_size,
    )
    result["year"] = year

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(output_file)


if __name__ == "__main__":
    main()
