# Data Cleaning

## Brand Mention Classifier

Classifies whether each tweet in a CSV is actually about the assigned brand.
The decision is driven primarily by `text` with contextual hints from other
columns such as annotations, mentions, hashtags, cashtags, and URLs.

### Requirements

- Python 3.11
- OpenRouter API key exported as `OPENROUTER_API_KEY`

### Run

```bash
export OPENROUTER_API_KEY="your_api_key"
python3 -m src.cli.classify_brand_mentions \
  --input data/input/tweets.csv \
  --output data/output/classified.csv \
  --model openrouter/your-model \
  --batch-size 100 \
  --progress-every 1 \
  --start-row 1
```

Optional JSONL output:

```bash
export OPENROUTER_API_KEY="your_api_key"
python3 -m src.cli.classify_brand_mentions \
  --input data/input/tweets.csv \
  --output data/output/classified.jsonl \
  --format jsonl \
  --model openrouter/your-model \
  --batch-size 100 \
  --progress-every 1 \
  --start-row 1
```

Resume from row 16701:

```bash
python3 -m src.cli.classify_brand_mentions \
  --input data/input/tweets.csv \
  --output data/output/classified_resume.csv \
  --model openrouter/your-model \
  --start-row 16701
```

Resume automatically from existing output rows:

```bash
python3 -m src.cli.classify_brand_mentions \
  --input data/input/tweets.csv \
  --output data/output/classified.csv \
  --model openrouter/your-model \
  --batch-size 100 \
  --progress-every 100 \
  --resume
```

### Output Columns

- `is_about_brand` (boolean)
- `confidence` (0.0-1.0)
- `rationale` (short string)

## Step 1: Dedupe By Text (Keep Highest Metrics)

```bash
python3 scripts/dedupe_by_text_keep_highest_metrics.py \
  --input data/input/tweets.csv \
  --output data/output/tweets_deduped.csv
```

This keeps one row per `text`, selecting the row with highest sum of:

- `public_metrics.retweet_count`
- `public_metrics.reply_count`
- `public_metrics.like_count`
- `public_metrics.quote_count`
- `public_metrics.bookmark_count`
- `public_metrics.impression_count`

## Step 2: Classify Dedupe + Apply To Original Copy

```bash
export OPENROUTER_API_KEY="your_api_key"
python3 scripts/classify_and_apply_to_original_copy.py \
  --input data/input/tweets.csv \
  --output data/output/tweets_classified_copy.csv \
  --model openrouter/your-model \
  --batch-size 100 \
  --progress-every 100
```

This script:

1. Dedupes by `text` keeping the highest-metrics row.
2. Runs LLM classification on the deduped rows.
3. Writes a copy of the original dataset with appended:
   - `is_about_brand`
   - `confidence`
   - `rationale`
