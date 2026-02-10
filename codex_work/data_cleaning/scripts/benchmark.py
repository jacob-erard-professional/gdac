import csv
import time
from pathlib import Path


def main() -> None:
    input_path = Path("data/input/tweets.csv")
    if not input_path.exists():
        raise SystemExit("Missing data/input/tweets.csv for benchmark")

    start = time.time()
    with input_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        count = sum(1 for _ in reader)
    duration = time.time() - start
    print(f"Loaded {count} rows in {duration:.2f}s")


if __name__ == "__main__":
    main()
