import csv
import time
from pathlib import Path

from src.lib.csv_io import is_true_like


def main() -> None:
    input_path = Path("data/input/tweets.csv")
    if not input_path.exists():
        raise SystemExit("Missing data/input/tweets.csv for benchmark")

    start = time.time()
    count = 0
    candidate_count = 0
    with input_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            count += 1
            if not is_true_like(row.get("is_about_brand")):
                candidate_count += 1
    duration = time.time() - start
    print(f"Loaded {count} rows in {duration:.2f}s")
    print(f"Candidate rows (non-true is_about_brand): {candidate_count}")


if __name__ == "__main__":
    main()
