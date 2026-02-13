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
python -m src.cli.classify_brand_mentions \
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
python -m src.cli.classify_brand_mentions \
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
python -m src.cli.classify_brand_mentions \
  --input data/input/tweets.csv \
  --output data/output/classified_resume.csv \
  --model openrouter/your-model \
  --start-row 16701
```

### Output Columns

- `is_about_brand` (boolean)
- `confidence` (0.0-1.0)
- `rationale` (short string)

## Extract Brand/Text/Label

```bash
python3 scripts/extract_brand_text_label.py \
  --input data/output/classified.csv \
  --output data/output/brand_text_labels.csv \
  --format csv
```

## Remove Duplicate Rows

```bash
python3 scripts/remove_duplicate_rows.py \
  --input 2026 tweets_2026-02-10.csv \
  --output tweets_2026-02-10_deduped.csv
```
