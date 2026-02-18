"""Pipeline module for schema orchestration and execution."""

from typing import Iterable, Dict, Tuple

# Canonical fields expected from the Twitter export used by this pipeline.
CANONICAL_REQUIRED_COLUMNS = {"id", "author_id", "created_at", "text"}
LEGACY_REQUIRED_COLUMNS = {"tweet_id", "user_id", "created_at", "text"}


def validate_columns(columns: Iterable[str]) -> Tuple[bool, set]:
    cols = set(columns)
    if CANONICAL_REQUIRED_COLUMNS.issubset(cols) or LEGACY_REQUIRED_COLUMNS.issubset(cols):
        return (True, set())
    missing = CANONICAL_REQUIRED_COLUMNS - cols
    return (False, missing)


def validate_row(row: Dict[str, str]) -> bool:
    row_id = row.get("id") or row.get("tweet_id")
    author_id = row.get("author_id") or row.get("user_id")
    created_at = row.get("created_at")
    text = row.get("text")
    return all(v not in (None, "") for v in (row_id, author_id, created_at, text))
