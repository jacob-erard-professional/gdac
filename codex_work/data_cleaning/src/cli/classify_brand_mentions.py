from __future__ import annotations

import argparse
import csv
import json
import logging
import time
from pathlib import Path
from typing import Callable, Dict, Any, Iterable, List

from src.lib.config import get_api_key
from src.lib.csv_io import read_csv_rows, parse_row
from src.lib.openrouter_client import call_openrouter
from src.lib.classifier import classify_batch


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Classify brand mentions in tweet CSVs.")
    parser.add_argument("--input", required=True, help="Path to input CSV")
    parser.add_argument("--output", required=True, help="Path to output file")
    parser.add_argument("--format", choices=["csv", "jsonl"], default="csv")
    parser.add_argument("--model", required=True, help="OpenRouter model identifier")
    parser.add_argument("--batch-size", type=int, default=100, help="Rows per batch")
    parser.add_argument("--progress-every", type=int, default=1, help="Log progress every N rows")
    parser.add_argument(
        "--start-row",
        type=int,
        default=1,
        help="1-based data row to start processing from (excluding CSV header)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help=(
            "Resume from existing output file by auto-calculating start row "
            "from already written rows"
        ),
    )
    return parser


def _chunked(iterable: Iterable[Dict[str, Any]], size: int) -> Iterable[List[Dict[str, Any]]]:
    batch: List[Dict[str, Any]] = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def _skip_rows(iterable: Iterable[Dict[str, Any]], rows_to_skip: int) -> Iterable[Dict[str, Any]]:
    if rows_to_skip <= 0:
        return iterable
    iterator = iter(iterable)
    for _ in range(rows_to_skip):
        try:
            next(iterator)
        except StopIteration:
            break
    return iterator


def _classify_batch_with_retries(
    batch: List[Dict[str, Any]],
    model: str,
    api_key: str,
    client: Callable[[str, str, list, int, Dict[str, Any] | None, list | None], Dict[str, Any]],
    max_retries: int = 5,
) -> list:
    tweets = [parse_row(row) for row in batch]
    attempt = 0
    while True:
        try:
            return classify_batch(tweets, model, api_key, client)
        except Exception as exc:  # noqa: BLE001
            attempt += 1
            if attempt > max_retries:
                raise RuntimeError(
                    f"Batch failed after {max_retries} retries: {exc}"
                ) from exc
            sleep_seconds = min(2 ** (attempt - 1), 30)
            logging.warning(
                "Batch request failed (attempt %s/%s). Retrying in %ss. Error: %s",
                attempt,
                max_retries,
                sleep_seconds,
                exc,
            )
            time.sleep(sleep_seconds)


def _count_existing_output_rows(output_path: Path, output_format: str) -> int:
    if not output_path.exists() or output_path.stat().st_size == 0:
        return 0
    if output_format == "jsonl":
        with output_path.open("r", encoding="utf-8") as handle:
            return sum(1 for line in handle if line.strip())
    with output_path.open("r", newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def run(
    args: argparse.Namespace,
    client: Callable[[str, str, list, int, Dict[str, Any] | None, list | None], Dict[str, Any]] = call_openrouter,
) -> None:
    if args.start_row < 1:
        raise ValueError("--start-row must be >= 1")

    logging.info("Starting batch classification")
    api_key = get_api_key()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    effective_start_row = args.start_row
    if args.resume:
        existing_rows = _count_existing_output_rows(output_path, args.format)
        resume_start_row = existing_rows + 1
        if resume_start_row > effective_start_row:
            effective_start_row = resume_start_row
        logging.info(
            "Resume enabled: detected %s existing rows in output; starting from row %s",
            existing_rows,
            effective_start_row,
        )

    rows_iter = read_csv_rows(args.input)
    rows_to_skip = effective_start_row - 1
    if rows_to_skip > 0:
        logging.info("Skipping %s rows; starting from row %s", rows_to_skip, effective_start_row)
        rows_iter = _skip_rows(rows_iter, rows_to_skip)

    processed = 0
    if args.format == "jsonl":
        with open(args.output, "a", encoding="utf-8") as handle:
            for batch in _chunked(rows_iter, max(1, args.batch_size)):
                results = _classify_batch_with_retries(batch, args.model, api_key, client, max_retries=5)
                for row, result in zip(batch, results):
                    output = {
                        **row,
                        "is_about_brand": result.is_about_brand,
                        "confidence": result.confidence,
                        "rationale": result.rationale,
                    }
                    handle.write(json.dumps(output, ensure_ascii=False) + "\n")
                    processed += 1
                    if args.progress_every > 0 and processed % args.progress_every == 0:
                        logging.info("Processed %s rows", processed)
    else:
        output_exists = output_path.exists() and output_path.stat().st_size > 0
        with open(args.output, "a", newline="", encoding="utf-8") as handle:
            writer = None
            for batch in _chunked(rows_iter, max(1, args.batch_size)):
                results = _classify_batch_with_retries(batch, args.model, api_key, client, max_retries=5)
                for row, result in zip(batch, results):
                    if writer is None:
                        fieldnames = list(row.keys())
                        for field in ["is_about_brand", "confidence", "rationale"]:
                            if field not in fieldnames:
                                fieldnames.append(field)
                        writer = csv.DictWriter(handle, fieldnames=fieldnames)
                        if not output_exists:
                            writer.writeheader()
                            output_exists = True
                    output = {
                        **row,
                        "is_about_brand": result.is_about_brand,
                        "confidence": result.confidence,
                        "rationale": result.rationale,
                    }
                    writer.writerow(output)
                    processed += 1
                    if args.progress_every > 0 and processed % args.progress_every == 0:
                        logging.info("Processed %s rows", processed)

    logging.info("Wrote %s rows to %s", processed, args.output)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = build_parser()
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
