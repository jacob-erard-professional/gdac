import random


def seed_random(seed: int) -> None:
    random.seed(seed)


def stable_sort_records(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=lambda r: (str(r.get("source_record_id", "")), str(r.get("text", ""))))
