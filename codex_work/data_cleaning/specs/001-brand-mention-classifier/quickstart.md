# Quickstart: Brand Mention Classifier

## Prerequisites

- Python 3.11
- `pytest` for running tests

## Input CSV Format

Required columns:
- `text`
- `brand`

Optional columns:
- Any other fields (used as context when disambiguating)

Parsed JSON-like columns (when present):
- `referenced_tweets`
- `entities.annotations`
- `entities.mentions`
- `entities.hashtags`
- `entities.cashtags`
- `entities.urls`

Metrics columns (missing values treated as `0`):
- `public_metrics.retweet_count`
- `public_metrics.reply_count`
- `public_metrics.like_count`
- `public_metrics.quote_count`
- `public_metrics.bookmark_count`
- `public_metrics.impression_count`

Missing/empty handling:
- If `text` or `brand` is missing/empty, the row is classified as
  `is_about_brand = false` with a rationale indicating missing input.

## Run (planned CLI)

```bash
export OPENROUTER_API_KEY="your_api_key"
python -m src.cli.classify_brand_mentions \
  --input data/input/tweets.csv \
  --output data/output/classified.csv \
  --model openrouter/your-model \
  --batch-size 100 \
  --progress-every 1
```

Optional JSONL output:

```bash
export OPENROUTER_API_KEY="your_api_key"
python -m src.cli.classify_brand_mentions \
  --input data/input/tweets.csv \
  --output data/output/classified.jsonl \
  --format jsonl \
  --model openrouter/your-model \
  --batch-size 100 \
  --progress-every 1
```

## Output Columns

- `is_about_brand` (boolean)
- `confidence` (0.0-1.0)
- `rationale` (short string)

## Notes

- The prompt prioritizes `text` and uses other columns only for context.
- JSON-like columns are parsed when present; malformed values are treated as
  empty lists.
- Update `README.md` with current functionality and how to run it when changes
  are made.
