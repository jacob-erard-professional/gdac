"""Utility script for celebrity share by brand operations."""

import argparse
import csv
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import pandas as pd

WHITESPACE_RE = re.compile(r"\s+")
MOJIBAKE_MARKERS = ("Ã", "Â", "â", "ðŸ", "à¸", "à¹", "Å")


def _repair_mojibake_once(value: str) -> str:
    text = str(value or "")
    if not any(marker in text for marker in MOJIBAKE_MARKERS):
        return text
    for enc in ("latin1", "cp1252"):
        try:
            repaired = text.encode(enc).decode("utf-8")
            before = sum(text.count(m) for m in MOJIBAKE_MARKERS)
            after = sum(repaired.count(m) for m in MOJIBAKE_MARKERS)
            if after < before:
                return repaired
        except Exception:
            continue
    return text


def _normalize_for_match(value: str) -> str:
    text = _repair_mojibake_once(str(value or ""))
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = WHITESPACE_RE.sub("", text)
    return text.lower()


def _as_true(value: object) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes", "y", "t"}


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


def _build_name_maps(names: list[str]) -> tuple[list[str], dict[str, str]]:
    canonical_to_display: dict[str, str] = {}
    for raw in names:
        canonical = _normalize_for_match(raw)
        if not canonical:
            continue
        canonical_to_display.setdefault(canonical, raw.strip())
    canonical_names = sorted(canonical_to_display.keys())
    if not canonical_names:
        raise ValueError("No valid celebrity names after normalization.")
    return canonical_names, canonical_to_display


def _resolve_column(columns: list[str], requested: str, candidates: list[str] | None = None) -> str:
    if requested in columns:
        return requested
    by_lower = {c.lower(): c for c in columns}
    if requested.lower() in by_lower:
        return by_lower[requested.lower()]
    for cand in candidates or []:
        if cand in columns:
            return cand
        if cand.lower() in by_lower:
            return by_lower[cand.lower()]
    raise ValueError(f"Required column not found: {requested}")


def compute_shares(
    input_file: Path,
    *,
    names: list[str],
    output_file: Path,
    brand_column: str,
    text_column: str,
    is_about_brand_column: str,
    chunk_size: int,
) -> int:
    canonical_names, canonical_to_display = _build_name_maps(names)

    denom_by_brand: dict[str, int] = defaultdict(int)
    celeb_hits: dict[tuple[str, str], int] = defaultdict(int)
    rows_scanned = 0

    brand_col = None
    text_col = None
    about_col = None

    for chunk in pd.read_csv(input_file, dtype=str, keep_default_na=False, chunksize=chunk_size):
        rows_scanned += len(chunk)
        cols = list(chunk.columns)
        if brand_col is None:
            brand_col = _resolve_column(cols, brand_column, ["brand", "Brands", "brand_tag", "brand_ad_name"])
            text_col = _resolve_column(cols, text_column, ["text"])
            about_col = _resolve_column(cols, is_about_brand_column, ["is_about_brand"])

        subset = chunk[chunk[about_col].map(_as_true)].copy()
        if subset.empty:
            continue

        for _, row in subset.iterrows():
            brand = str(row.get(brand_col, "")).strip()
            if not brand:
                continue
            denom_by_brand[brand] += 1
            text_norm = _normalize_for_match(row.get(text_col, ""))
            if not text_norm:
                continue

            matched = {canonical_to_display[c] for c in canonical_names if c in text_norm}
            for celeb in matched:
                celeb_hits[(brand, celeb)] += 1

    output_file.parent.mkdir(parents=True, exist_ok=True)
    rows_out = []
    for (brand, celeb), count in celeb_hits.items():
        denom = denom_by_brand.get(brand, 0)
        if denom <= 0:
            continue
        rows_out.append(
            {
                "brand": brand,
                "celebrity": celeb,
                "share_of_tweets_with_celebrity": round(count / denom, 6),
            }
        )
    rows_out.sort(
        key=lambda item: (
            str(item["brand"]).lower(),
            -float(item["share_of_tweets_with_celebrity"]),
            str(item["celebrity"]).lower(),
        )
    )

    with output_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["brand", "celebrity", "share_of_tweets_with_celebrity"],
        )
        writer.writeheader()
        writer.writerows(rows_out)

    return rows_scanned


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Compute celebrity share by brand from rows where is_about_brand=true. "
            "Output columns: brand, celebrity, share_of_tweets_with_celebrity."
        )
    )
    parser.add_argument("--year", type=str, help="Year under sentiment/bertweet/<year>/")
    parser.add_argument("--input-file", type=Path, help="Explicit input CSV path")
    parser.add_argument("--output-file", type=Path, help="Output CSV path")
    parser.add_argument("--names", type=str, help='Comma-separated celebrity names')
    parser.add_argument("--names-file", type=Path, help="Path to names .txt (one per line)")
    parser.add_argument("--celebrities-file", type=Path, help="Alias for --names-file")
    parser.add_argument("--brand-column", type=str, default="brand")
    parser.add_argument("--text-column", type=str, default="text")
    parser.add_argument("--is-about-brand-column", type=str, default="is_about_brand")
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
        output_file = base_dir / "outputs" / "analytics" / args.year / "celebrity_share_by_brand.csv"
    elif not output_file.is_absolute():
        output_file = (base_dir / output_file).resolve()

    names = _load_names(args)
    rows_scanned = compute_shares(
        input_file,
        names=names,
        output_file=output_file,
        brand_column=args.brand_column,
        text_column=args.text_column,
        is_about_brand_column=args.is_about_brand_column,
        chunk_size=args.chunk_size,
    )
    print(f"rows_scanned={rows_scanned}")
    print(output_file)


if __name__ == "__main__":
    main()
