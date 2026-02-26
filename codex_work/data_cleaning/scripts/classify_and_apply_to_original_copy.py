import argparse
import csv
from pathlib import Path

from scripts.dedupe_by_text_keep_highest_metrics import dedupe_rows
from src.cli.classify_brand_mentions import run


def _classification_by_text(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        mapping: dict[str, dict[str, str]] = {}
        for row in reader:
            text = (row.get("text") or "").strip()
            mapping[text] = {
                "is_about_brand": row.get("is_about_brand", "False"),
                "confidence": row.get("confidence", "0.0"),
                "rationale": row.get("rationale", "Missing classification"),
            }
    return mapping


def _write_original_copy_with_labels(
    original_input: Path,
    output_copy: Path,
    classifications: dict[str, dict[str, str]],
) -> int:
    with original_input.open("r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames or []
        extra_columns = ["is_about_brand", "confidence", "rationale"]
        final_fieldnames = fieldnames + [c for c in extra_columns if c not in fieldnames]

        with output_copy.open("w", newline="", encoding="utf-8") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=final_fieldnames)
            writer.writeheader()
            written = 0
            for row in reader:
                text = (row.get("text") or "").strip()
                labels = classifications.get(
                    text,
                    {
                        "is_about_brand": "False",
                        "confidence": "0.0",
                        "rationale": "Missing dedupe classification",
                    },
                )
                writer.writerow({**row, **labels})
                written += 1
    return written


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Two-step workflow: dedupe by text (keep highest metric sum), then run "
            "brand mention classification on deduped rows and apply labels to a copy "
            "of the original dataset."
        )
    )
    parser.add_argument("--input", required=True, help="Original input CSV path")
    parser.add_argument(
        "--output",
        required=True,
        help="Output CSV path for original dataset copy with appended label columns",
    )
    parser.add_argument("--model", required=True, help="OpenRouter model identifier")
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--progress-every", type=int, default=100)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--work-dir",
        default="data/output/workflow_tmp",
        help="Directory for intermediate deduped/classified files",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    work_dir = Path(args.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    deduped_path = work_dir / "deduped.csv"
    dedupe_rows(input_path, deduped_path)

    deduped_classified_path = work_dir / "deduped_classified.csv"
    classify_args = argparse.Namespace(
        input=str(deduped_path),
        output=str(deduped_classified_path),
        format="csv",
        model=args.model,
        batch_size=args.batch_size,
        progress_every=args.progress_every,
        start_row=1,
        resume=args.resume,
    )
    run(classify_args)

    classifications = _classification_by_text(deduped_classified_path)
    written = _write_original_copy_with_labels(input_path, output_path, classifications)
    print(f"Wrote {written} rows to {output_path}")


if __name__ == "__main__":
    main()
