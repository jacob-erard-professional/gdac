import csv
import gzip
import re
from pathlib import Path
from typing import Iterator

from src.common.io.storage import read_jsonl


def run(raw_path: str, event_name: str, year: int) -> list[dict]:
    rows = read_jsonl(raw_path)
    if rows:
        return rows
    # Deterministic fallback fixture when raw feed is absent.
    return [
        {
            "source_record_id": f"{year}-1",
            "event_name": event_name,
            "year": year,
            "text": f"{event_name} touchdown",
        },
        {
            "source_record_id": f"{year}-2",
            "event_name": event_name,
            "year": year,
            "text": "",
        },
    ]


def iter_chunks(
    *,
    raw_root: str,
    event_name: str,
    year: int,
    input_format: str = "jsonl",
    chunk_size: int = 100_000,
    csv_delimiter: str = ",",
    csv_encoding: str = "utf-8",
    csv_columns: dict | None = None,
) -> Iterator[list[dict]]:
    def _first_matching(path: Path, pattern: str) -> Path | None:
        matches = sorted(path.glob(pattern))
        return matches[0] if matches else None

    def _resolve_input_path() -> tuple[str, Path | None]:
        base = Path(raw_root) / event_name / str(year)
        if input_format == "csv":
            preferred = base / "posts.csv"
            if preferred.exists():
                return "csv", preferred
            gz = base / "posts.csv.gz"
            if gz.exists():
                return "csv.gz", gz
            any_csv = _first_matching(base, "*.csv")
            if any_csv:
                return "csv", any_csv
            any_gz = _first_matching(base, "*.csv.gz")
            if any_gz:
                return "csv.gz", any_gz
            return "csv", None

        # jsonl preferred; auto-fallback to csv when jsonl missing.
        preferred = base / "posts.jsonl"
        if preferred.exists():
            return "jsonl", preferred
        any_jsonl = _first_matching(base, "*.jsonl")
        if any_jsonl:
            return "jsonl", any_jsonl
        any_csv = _first_matching(base, "*.csv")
        if any_csv:
            return "csv", any_csv
        any_gz = _first_matching(base, "*.csv.gz")
        if any_gz:
            return "csv.gz", any_gz
        return "jsonl", None

    def _coerce_year(raw: object, default_year: int) -> int:
        text = str(raw).strip()
        if not text:
            return default_year
        # Direct integer-like values.
        if text.isdigit():
            return int(text)
        # Common timestamp/date strings (e.g., 2023-02-13T..., 2/11/2023 14:13:37).
        match = re.search(r"(19|20)\d{2}", text)
        if match:
            return int(match.group(0))
        return default_year

    resolved_mode, resolved_path = _resolve_input_path()

    if resolved_mode == "jsonl":
        path = str(resolved_path) if resolved_path else f"{raw_root}/{event_name}/{year}/posts.jsonl"
        rows = run(path, event_name, year)
        yield rows
        return

    if resolved_mode not in {"csv", "csv.gz"}:
        raise ValueError(f"Unsupported input format: {input_format}")

    csv_path = resolved_path
    if csv_path is None or not csv_path.exists():
        # Keep deterministic fallback behavior for empty local environments.
        yield [
            {
                "source_record_id": f"{year}-1",
                "event_name": event_name,
                "year": year,
                "text": f"{event_name} touchdown",
            },
            {
                "source_record_id": f"{year}-2",
                "event_name": event_name,
                "year": year,
                "text": "",
            },
        ]
        return

    mapping = csv_columns or {
        "source_record_id": "source_record_id",
        "event_name": "event_name",
        "year": "year",
        "text": "text",
        "brand_ad_name": "brand_ad_name",
        "retweet_count": "public_metrics.retweet_count",
        "like_count": "public_metrics.like_count",
        "reply_count": "public_metrics.reply_count",
        "quote_count": "public_metrics.quote_count",
        "hashtags": "entities.hashtags",
        "mentions": "entities.mentions",
    }
    current: list[dict] = []
    opener = gzip.open if resolved_mode == "csv.gz" else open
    with opener(csv_path, "rt", encoding=csv_encoding, newline="") as f:
        reader = csv.DictReader(f, delimiter=csv_delimiter)
        for row in reader:
            current.append(
                {
                    "source_record_id": str(row.get(mapping["source_record_id"], "")).strip(),
                    "event_name": str(row.get(mapping["event_name"], event_name)).strip() or event_name,
                    "year": _coerce_year(row.get(mapping["year"], year), year),
                    "text": str(row.get(mapping["text"], "")),
                    "brand_ad_name": str(row.get(mapping.get("brand_ad_name", ""), "")).strip(),
                    "retweet_count": str(row.get(mapping.get("retweet_count", ""), "0")),
                    "like_count": str(row.get(mapping.get("like_count", ""), "0")),
                    "reply_count": str(row.get(mapping.get("reply_count", ""), "0")),
                    "quote_count": str(row.get(mapping.get("quote_count", ""), "0")),
                    "raw_hashtags": str(row.get(mapping.get("hashtags", ""), "")),
                    "raw_mentions": str(row.get(mapping.get("mentions", ""), "")),
                }
            )
            if len(current) >= chunk_size:
                yield current
                current = []
    if current:
        yield current
