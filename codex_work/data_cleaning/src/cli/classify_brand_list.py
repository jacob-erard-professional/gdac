from __future__ import annotations

import argparse
import csv
import json
import logging
from typing import Any, Dict, Iterable, List, Callable

from src.lib.brand_list_classifier import classify_brand_list_batch, merge_brand_list_output, skipped_result
from src.lib.config import get_api_key
from src.lib.csv_io import is_true_like, load_brand_list_csv, read_csv_rows
from src.lib.openrouter_client import call_openrouter


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Classify tweets against a candidate brand list.")
    parser.add_argument("--input", required=True, help="Path to input tweet CSV")
    parser.add_argument("--brand-list", required=True, help="Path to one-column brand CSV with header 'brand'")
    parser.add_argument("--output", required=True, help="Path to output file")
    parser.add_argument("--format", choices=["csv", "jsonl"], default="csv")
    parser.add_argument("--model", required=True, help="OpenRouter model identifier")
    parser.add_argument("--batch-size", type=int, default=100, help="Rows per classification batch")
    parser.add_argument("--progress-every", type=int, default=1, help="Log progress every N rows")
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


def _write_output_row(
    out_handle,
    out_format: str,
    writer,
    fieldnames: List[str],
    output_row: Dict[str, Any],
):
    if out_format == "jsonl":
        out_handle.write(json.dumps(output_row, ensure_ascii=False) + "\n")
        return writer, fieldnames

    if writer is None:
        fieldnames = list(output_row.keys())
        writer = csv.DictWriter(out_handle, fieldnames=fieldnames)
        writer.writeheader()
    writer.writerow(output_row)
    return writer, fieldnames


def run(
    args: argparse.Namespace,
    client: Callable[[str, str, list, int, Dict[str, Any] | None, list | None], Dict[str, Any]] = call_openrouter,
) -> None:
    logging.info("Starting brand-list classification")
    api_key = get_api_key()
    candidate_brands = load_brand_list_csv(args.brand_list)
    rows_iter = read_csv_rows(args.input)

    processed = 0
    classified = 0
    skipped = 0

    mode = "w"
    newline = "" if args.format == "csv" else None
    with open(args.output, mode, newline=newline, encoding="utf-8") as out_handle:
        writer = None
        fieldnames: List[str] = []

        for batch in _chunked(rows_iter, max(1, args.batch_size)):
            candidate_rows: List[Dict[str, Any]] = []
            candidate_indexes: List[int] = []
            batch_results: List[Dict[str, Any]] = [skipped_result() for _ in batch]

            for idx, row in enumerate(batch):
                if is_true_like(row.get("is_about_brand")):
                    skipped += 1
                    continue
                candidate_rows.append(row)
                candidate_indexes.append(idx)

            if candidate_rows:
                classified_results = classify_brand_list_batch(
                    candidate_rows,
                    candidate_brands,
                    args.model,
                    api_key,
                    client,
                )
                classified += len(classified_results)
                for row_idx, result in zip(candidate_indexes, classified_results):
                    batch_results[row_idx] = result

            for row, result in zip(batch, batch_results):
                output_row = merge_brand_list_output(row, result)
                writer, fieldnames = _write_output_row(
                    out_handle,
                    args.format,
                    writer,
                    fieldnames,
                    output_row,
                )
                processed += 1
                if args.progress_every > 0 and processed % args.progress_every == 0:
                    logging.info("Processed %s rows (classified=%s skipped=%s)", processed, classified, skipped)

    logging.info("Wrote %s rows to %s", processed, args.output)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = build_parser()
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
