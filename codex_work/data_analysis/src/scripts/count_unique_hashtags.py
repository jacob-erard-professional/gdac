import argparse
import json
from pathlib import Path


def count_unique_hashtags(input_file: Path) -> dict:
    payload = json.loads(input_file.read_text(encoding="utf-8"))
    hashtags = payload.get("hashtags", [])
    if not isinstance(hashtags, list):
        raise ValueError(f"Invalid hashtags_frequency shape in {input_file}: 'hashtags' must be a list")

    unique = set()
    for item in hashtags:
        if not isinstance(item, dict):
            continue
        tag = str(item.get("hashtag", "")).strip().lower()
        if tag:
            unique.add(tag)

    return {
        "source_file": str(input_file),
        "year": payload.get("year"),
        "unique_hashtag_count": int(len(unique)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Count unique hashtags from hashtags_frequency.json"
    )
    parser.add_argument("--year", type=str, help="Year under outputs/analytics/<year>/")
    parser.add_argument("--input-file", type=Path, help="Explicit hashtags_frequency JSON path")
    parser.add_argument("--output-file", type=Path, help="Optional output JSON path")
    args = parser.parse_args()

    if bool(args.year) == bool(args.input_file):
        raise ValueError("Provide exactly one of --year or --input-file")

    base_dir = Path(__file__).resolve().parents[2]
    input_file = args.input_file
    year = args.year
    if input_file is None:
        input_file = base_dir / "outputs" / "analytics" / year / "hashtags_frequency.json"
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    result = count_unique_hashtags(input_file)
    print(result["unique_hashtag_count"])

    output_file = args.output_file
    if output_file is None and year is not None:
        output_file = base_dir / "outputs" / "analytics" / year / "unique_hashtag_count.json"
    if output_file is not None:
        if not output_file.is_absolute():
            output_file = (base_dir / output_file).resolve()
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
        print(output_file)


if __name__ == "__main__":
    main()
