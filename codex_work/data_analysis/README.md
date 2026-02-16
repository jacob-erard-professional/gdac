# Super Bowl Twitter Data Analysis

This repository contains a deterministic, stage-based CLI pipeline for year-scoped
Twitter Super Bowl analysis, plus optional LLM-driven grouping and sentiment analysis.

## Directory Scope Rule

All work for this project remains inside the `data_analysis` directory. Add new
subdirectories here when needed.

## Data Layout

```text
data/
  raw/<year>/*.csv
  processed/<year>/
  enriched/<year>/
outputs/
  analytics/<year>/
  aux/<year>/   # maps, partial JSONLs, recovery artifacts, joined parquet maps
sentiment/
  bertweet/<year>/sentiment.json
```

Raw files are immutable after ingest.

## Quickstart

Single stage:

```bash
.venv/bin/python -m src.cli run --year 2024 --stage clean
```

Single stage (same, using an explicit raw folder):

```bash
.venv/bin/python -m src.cli run --data-dir data/raw/2024 --stage clean
```

Full pipeline (one year):

```bash
.venv/bin/python -m src.cli run --year 2024 --all
```

Full pipeline (same, using an explicit raw folder):

```bash
.venv/bin/python -m src.cli run --all --data-dir data/raw/2024
```

Full pipeline + BERTweet sentiment:

```bash
.venv/bin/python -m src.cli run --year 2024 --all --with-sentiment
```

Full pipeline + parent-company joins:

```bash
.venv/bin/python -m src.cli run --year 2024 --all --with-sentiment --with-parent-company-sentiment
```

Run all available workflows (pipeline + sentiment + grouping + maps + breakdowns):

```bash
.venv/bin/python -m src.cli run-everything --data-dir data/raw/2024 --grouping-model openai/gpt-4.1
```

Optional: clean analytics outputs before re-running analysis stages:

```bash
.venv/bin/python -m src.cli run-everything --data-dir data/raw/2024 --clean-outputs
```

Optional: supply parent-company hints to improve grouping of franchise brands:

```bash
.venv/bin/python -m src.cli group-parent-companies --year 2024 --hints-file config/parent_company_hints.json
```

Optional: supply brand-group hints to improve brand grouping:

```bash
.venv/bin/python -m src.cli group-brands --year 2024 --hints-file config/brand_group_hints.json
```

Run everything except selected workflows (repeat `--exclude`):

```bash
.venv/bin/python -m src.cli run-everything --data-dir data/raw/2024 --grouping-model openai/gpt-4.1 --exclude group-parent-companies
```

Valid excludes: `sentiment`, `ad-sentiment`, `parent-company-sentiment`, `agentic-emotion`, `group-brands`, `group-parent-companies`,
`sentiment-maps`, `emotion-breakdowns`.
Note: `ad-sentiment` requires `sentiment` (hard error if excluded).
By default `run` and `run-everything` preserve existing analytics outputs. Use `--clean-outputs`
only when you explicitly want to clear `outputs/analytics/<year>/` before analysis.
Grouping workflows require `--grouping-model`. Agentic emotion requires `--agentic-emotion-model`.

Run mode selection notes:
- `run --all` accepts `--year` or `--data-dir` (or neither to run all discovered years).
- `run --stage` requires exactly one of `--year` or `--data-dir`.
- `run-everything` requires `--data-dir` and does not accept `--year`.
- `--data-dir` may point to either `data/raw/YYYY` or `data/raw/YYYY_full`.

## Stages

- ingest: schema validation from `data/raw/<year>/` to `data/processed/<year>/ingested.csv`
- clean: dedupe/null/timestamp normalization to `data/processed/<year>/cleaned.csv`
  (includes canonical Twitter fields such as `id`, `author_id`, `conversation_id`,
  `entities.*`, `public_metrics.*`, `username`, and `name`; adds `pipeline_row_id`)
- process: text features/tags to `data/enriched/<year>/enriched.csv`
- analyze: analytics artifact generation under `outputs/analytics/<year>/`
- sentiment (optional): BERTweet sentiment inference → `sentiment/bertweet/<year>/sentiment.json`
- ad_sentiment (optional): joins sentiment + enriched rows → ad-level outputs
- parent_company_sentiment (optional): joins sentiment + parent company groupings
- visualize (optional): placeholder visualization output
- export (optional): placeholder export artifact

## LLM Grouping Workflows

Brand-grouping (hashtags → brands):

```bash
cp .env.example .env
export OPENROUTER_API_KEY=... # keep local only; never commit
.venv/bin/python -m src.cli group-brands --year 2024 --model openai/gpt-4.1
```

Parent-company grouping (brands → parent companies):

```bash
.venv/bin/python -m src.cli group-parent-companies --year 2024 --model openai/gpt-4.1
```

Notes:
- `config/parent_company_overrides.json` is applied before LLM mapping.
- Both grouping workflows support `--resume` (default) and `--no-resume`.
- Partial JSONLs and parse failures go to `outputs/aux/<year>/`.
- All agentic workflows enforce minimum throttling and retries (2.5s delay, 12 retries).
- On rate-limit or parse failure, you’ll be prompted to enter a new model ID.

## Sentiment Workflows

BERTweet sentiment:

```bash
.venv/bin/python -m src.cli sentiment --year 2024 --batch-size 64
```

Outputs:
- `sentiment/bertweet/<year>/tweets_with_sentiement.csv` (copy of source rows with appended `sentiment` and `confidence` columns)
- `sentiment/bertweet/<year>/sentiment.json` (metadata + records for downstream compatibility)

Default source for `sentiment --year/--data-dir` is `data/processed/<partition>/ingested.csv` so original ingested columns are retained in the CSV output.

Agentic emotion classification (committee + supervisor):

```bash
.venv/bin/python -m src.cli agentic-emotion --year 2024 --model openai/gpt-4.1 --batch-size 40
```

Optional brand filter:

```bash
.venv/bin/python -m src.cli agentic-emotion --year 2024 --model openai/gpt-4.1 --brand-filter "marvel,disney"
```

GPU usage:
- Defaults to CUDA if available (falls back to CPU).
- Override with `--device cpu` for the CLI, or `--sentiment-device` for `run`.

## Mapping & Aggregation Scripts

Match sentiment tweets to brands and parent companies (from hashtags in the sentiment text):

```bash
.venv/bin/python -m src.scripts.match_sentiment_to_companies \
  --sentiment-file sentiment/bertweet/2024/sentiment.json \
  --brand-groups-file outputs/analytics/2024/brand_groups.json \
  --parent-groups-file outputs/analytics/2024/parent_company_groups.json \
  --output-file outputs/aux/2024/sentiment_company_map.jsonl \
  --batch-size 1000
```

Brand source rule:
- Sentiment-company mapping now uses the sentiment record `brand` (carried from raw CSV
  `brand`/`brand_ad_name`) as the primary brand signal.
- Hashtag-to-brand matching is only a fallback when `brand` is missing/empty.

Same, but choose which label field to store (e.g., `sentiment`):

```bash
.venv/bin/python -m src.scripts.match_sentiment_to_companies_by_label \
  --sentiment-file sentiment/bertweet/2024/sentiment_reclassified.json \
  --brand-groups-file outputs/analytics/2024/brand_groups.json \
  --parent-groups-file outputs/analytics/2024/parent_company_groups.json \
  --output-file outputs/aux/2024/sentiment_company_map.jsonl \
  --label-field sentiment \
  --batch-size 1000
```

Batch match tweets to parent companies directly from enriched data:

```bash
.venv/bin/python -m src.scripts.match_tweets_to_parent_company \
  --enriched-file data/enriched/2024/enriched.csv \
  --brand-groups-file outputs/analytics/2024/brand_groups.json \
  --parent-groups-file outputs/analytics/2024/parent_company_groups.json \
  --output-file outputs/aux/2024/parent_company_tweet_map.jsonl \
  --year 2024 \
  --batch-size 1000
```

Emotion breakdowns from sentiment-company maps:

```bash
.venv/bin/python -m src.scripts.emotion_breakdown \
  --input-jsonl outputs/aux/2024/sentiment_company_map.jsonl \
  --parent-out outputs/aux/2024/parent_company_sentiment_breakdown.json \
  --brand-out outputs/aux/2024/brand_sentiment_breakdown.json
```

Reclassify sentiment by confidence (keep both datasets):

```bash
.venv/bin/python -m src.scripts.reclassify_sentiment_by_confidence \
  --input-file sentiment/bertweet/2024/sentiment.json \
  --output-file sentiment/bertweet/2024/sentiment_reclassified.json \
  --threshold 0.65 \
  --label-field sentiment
```

Other helper scripts:
- `src/scripts/split_raw_csv.py` (first N rows of raw data)
- `src/scripts/split_cleaned_csv.py` (first N rows of cleaned data)
- `src/scripts/split_hashtags_frequency.py` (first N hashtags for grouping)
- `src/scripts/recover_grouping_from_partial.py` (rebuild groups from partial JSONL)

## Visualization Website

The `site/` folder contains a React comparison dashboard for regular vs full datasets.

Quickstart:

```bash
cd site
npm install
npm run dev
```

The site reads artifacts from:
- `outputs/analytics/<year>/` (regular)
- `outputs/analytics/<year>_full/` (full)
- `data/raw/<year>/` and `data/raw/<year>_full/` (brand frequency + tweet cards)

Current behavior:
- Top dropdown lists only years where both regular and full analytics folders exist.
- Required word clouds:
  - Full combined hashtag+parent-group cloud.
  - Celebrity clouds for regular and full (`celebrity_freq.csv`).
  - Raw brand-frequency clouds for regular and full (`brand` column counts).
- Example tweet cards:
  - One card for regular and one for full, both with arrow navigation and index/total display.
  - Duplicate tweet text is removed per card.
  - Full card includes only rows with `is_about_brand=false`; if column is missing it is treated as `false`.

## ID Flow Diagram

```
ingest -> clean (adds pipeline_row_id)
              |
              v
          processed/cleaned.csv
              |
              v
          enriched/enriched.csv
              |
              +--> sentiment/bertweet/sentiment.json (pipeline_row_id)
              |
              +--> brand_groups.json + parent_company_groups.json
                        |
                        v
          parent_company_tweet_map.json(.jsonl)
              |
              v
   parent_company_*_sentiment_* joins on pipeline_row_id
```

## Outputs

Analytics outputs (`outputs/analytics/<year>/`):
- `hashtags_frequency.json`
- `mentions_frequency.json`
- `brand_groups.json`
- `parent_company_groups.json`
- `ad_sentiment_joined.parquet`
- `ad_sentiment_summary.json`
- `ad_sentiment_summary.csv`
- `parent_company_sentiment_joined.parquet`
- `parent_company_sentiment_summary.json`
- `parent_company_sentiment_summary.csv`
- `parent_company_sentiment_timeslices.json`
- `parent_company_sentiment_timeslices.csv`
- `parent_company_sentiment_by_ad_tag.json`
- `parent_company_sentiment_by_ad_tag.csv`

Auxiliary outputs (`outputs/aux/<year>/`, gitignored):
- `brand_tweet_map.json`
- `parent_company_tweet_map.json`
- `*_partial.jsonl`
- `*_parse_failures.txt`
- `*_recovered.json`
- `sentiment_company_map.jsonl`
- `parent_company_tweet_map.jsonl`
- `*_emotion_breakdown.json`

Sentiment outputs:
- `sentiment/bertweet/<year>/sentiment.json`
- `sentiment/bertweet/<year>/sentiment_reclassified.json`

## Models

BERTweet sentiment:
- Default: `finiteautomata/bertweet-base-sentiment-analysis`
- Fallback (explicit): `rabindralamsal/finetuned-bertweet-sentiment-analysis`

## Notes

- Sentiment confidence gate: outputs are reclassified to `neutral` when confidence < 0.65.
- `run-everything` assumes `OPENROUTER_API_KEY` is set for grouping workflows.
- `--data-dir` is treated as the explicit raw-input directory for that run (it is not rewritten).
