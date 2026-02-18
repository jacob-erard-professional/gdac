"""Utility script for filter rows by celebrity operations."""

import argparse
import re
import unicodedata
from pathlib import Path

import pandas as pd

WHITESPACE_RE = re.compile(r"\s+")
MOJIBAKE_MARKERS = ("Ã", "Â", "â", "ðŸ", "à¸", "à¹", "Å")


def _strip_all_whitespace(value: str) -> str:
    return WHITESPACE_RE.sub("", str(value))


def _repair_mojibake_once(value: str) -> str:
    text = str(value or "")
    if not any(marker in text for marker in MOJIBAKE_MARKERS):
        return text
    for enc in ("latin1", "cp1252"):
        try:
            repaired = text.encode(enc).decode("utf-8")
            if sum(text.count(m) for m in MOJIBAKE_MARKERS) > sum(repaired.count(m) for m in MOJIBAKE_MARKERS):
                return repaired
        except Exception:
            continue
    return text


def _normalize_for_match(value: str) -> str:
    text = _repair_mojibake_once(str(value or ""))
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return _strip_all_whitespace(text).lower()


def _build_name_maps(names: list[str]) -> tuple[list[str], dict[str, str]]:
    cleaned_names = [name.strip() for name in names if name.strip()]
    if not cleaned_names:
        raise ValueError("At least one non-empty celebrity name is required.")

    canonical_to_display: dict[str, str] = {}
    for name in cleaned_names:
        canonical = _normalize_for_match(name)
        if not canonical:
            continue
        canonical_to_display.setdefault(canonical, name)

    canonical_names = sorted(canonical_to_display.keys())
    if not canonical_names:
        raise ValueError("At least one non-empty celebrity name is required.")
    return canonical_names, canonical_to_display


def filter_rows_by_celebrity(
    input_file: Path,
    *,
    names: list[str],
    output_file: Path,
    text_column: str = "text",
    sentiment_column: str = "sentiment",
    confidence_column: str = "confidence",
    output_name_column: str = "celebrity_names",
    chunk_size: int = 100_000,
) -> int:
    canonical_names, canonical_to_display = _build_name_maps(names)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    if output_file.exists():
        output_file.unlink()

    rows_written = 0
    first_chunk = True

    for chunk in pd.read_csv(input_file, dtype=str, keep_default_na=False, chunksize=chunk_size):
        if text_column not in chunk.columns:
            raise ValueError(f"Input file missing required column: {text_column}")
        if sentiment_column not in chunk.columns:
            raise ValueError(f"Input file missing required column: {sentiment_column}")
        if confidence_column not in chunk.columns:
            raise ValueError(f"Input file missing required column: {confidence_column}")

        text_norm = chunk[text_column].astype(str).map(_normalize_for_match)
        matched_names: list[list[str]] = []
        keep_mask = []

        for value in text_norm.tolist():
            hit = [canonical_to_display[c] for c in canonical_names if c in value]
            keep_mask.append(bool(hit))
            matched_names.append(hit)

        if not any(keep_mask):
            continue

        matched = chunk.loc[keep_mask, [text_column, sentiment_column, confidence_column]].copy()
        matched[output_name_column] = [names_for_row for names_for_row, keep in zip(matched_names, keep_mask) if keep]
        matched = matched.explode(output_name_column)
        matched = matched.rename(
            columns={
                text_column: "text",
                sentiment_column: "sentiment",
                confidence_column: "confidence",
            }
        )
        matched = matched[["text", "sentiment", "confidence", output_name_column]]

        rows_written += int(len(matched))
        matched.to_csv(
            output_file,
            mode="w" if first_chunk else "a",
            index=False,
            header=first_chunk,
        )
        first_chunk = False

    return rows_written


def _load_names(args) -> list[str]:
    names_file = args.names_file or args.celebrities_file
    if not args.names and not names_file:
        raise ValueError("Provide one of --names, --names-file, or --celebrities-file")
    if args.names and names_file:
        raise ValueError("Provide only one of --names, --names-file, or --celebrities-file")
    if args.names_file and args.celebrities_file:
        raise ValueError("Provide only one of --names-file or --celebrities-file")

    if names_file:
        if not names_file.exists():
            raise FileNotFoundError(f"Names file not found: {names_file}")
        return [line.strip() for line in names_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [part.strip() for part in args.names.split(",") if part.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Filter sentiment-enriched rows by celebrity name matches in text and output "
            "text/sentiment/celebrity_names CSV."
        )
    )
    parser.add_argument("--year", type=str, help="Partition under sentiment/bertweet/<year>/")
    parser.add_argument("--input-file", type=Path, help="Explicit sentiment-enriched CSV path")
    parser.add_argument(
        "--names",
        type=str,
        help='Comma-separated names (example: "beyonce,taylor swift,kevin hart")',
    )
    parser.add_argument("--names-file", type=Path, help="Path to .txt file with one celebrity per line")
    parser.add_argument(
        "--celebrities-file",
        type=Path,
        help="Alias for --names-file. Path to .txt file with one celebrity per line",
    )
    parser.add_argument("--output-file", type=Path, help="Output CSV path")
    parser.add_argument("--text-column", type=str, default="text")
    parser.add_argument("--sentiment-column", type=str, default="sentiment")
    parser.add_argument("--confidence-column", type=str, default="confidence")
    parser.add_argument("--output-name-column", type=str, default="celebrity_names")
    parser.add_argument("--chunk-size", type=int, default=100_000)
    args = parser.parse_args()

    if bool(args.year) == bool(args.input_file):
        raise ValueError("Provide exactly one of --year or --input-file")

    base_dir = Path(__file__).resolve().parents[2]
    input_file = args.input_file
    if input_file is None:
        input_file = base_dir / "sentiment" / "bertweet" / args.year / "tweets_with_sentiement.csv"
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    output_file = args.output_file
    if output_file is None:
        if args.year is None:
            raise ValueError("Provide --output-file when using --input-file")
        output_file = base_dir / "outputs" / "analytics" / args.year / "celebrity_sentiment_rows.csv"
    elif not output_file.is_absolute():
        output_file = (base_dir / output_file).resolve()

    names = _load_names(args)
    rows_written = filter_rows_by_celebrity(
        input_file,
        names=names,
        output_file=output_file,
        text_column=args.text_column,
        sentiment_column=args.sentiment_column,
        confidence_column=args.confidence_column,
        output_name_column=args.output_name_column,
        chunk_size=args.chunk_size,
    )
    print(f"rows_written={rows_written}")
    print(output_file)


if __name__ == "__main__":
    main()
