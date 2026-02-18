"""Shared utilities for io."""

import csv
from pathlib import Path
from typing import Dict, Iterable, Iterator, List


def chunked_csv_reader(path: Path, chunk_size: int = 5000) -> Iterator[List[Dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        buf = []
        for row in reader:
            buf.append(row)
            if len(buf) >= chunk_size:
                yield buf
                buf = []
        if buf:
            yield buf


def stable_sort_rows(rows: Iterable[Dict[str, str]], key: str = "tweet_id"):
    return sorted(rows, key=lambda r: (r.get(key, ""), r.get("created_at", "")))


def write_csv(path: Path, rows: List[Dict[str, str]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
