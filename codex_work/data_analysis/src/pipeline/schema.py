from typing import Iterable, Dict, Tuple

REQUIRED_COLUMNS = {"tweet_id", "created_at", "text", "user_id"}


def validate_columns(columns: Iterable[str]) -> Tuple[bool, set]:
    cols = set(columns)
    missing = REQUIRED_COLUMNS - cols
    return (len(missing) == 0, missing)


def validate_row(row: Dict[str, str]) -> bool:
    return all(row.get(c) not in (None, "") for c in REQUIRED_COLUMNS)
