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
  deep/<year>/deep_sentiment.json
```

Raw files are immutable after ingest.

## Quickstart

Single stage:

```bash
.venv/bin/python -m src.cli run --year 2024 --stage clean
```

Full pipeline (one year):

```bash
.venv/bin/python -m src.cli run --year 2024 --all
```

Full pipeline + BERTweet sentiment:

```bash
.venv/bin/python -m src.cli run --year 2024 --all --with-sentiment
```

Full pipeline + deep sentiment:

```bash
.venv/bin/python -m src.cli run --year 2024 --all --with-deep-sentiment
```

Full pipeline + parent-company joins:

```bash
.venv/bin/python -m src.cli run --year 2024 --all --with-sentiment --with-parent-company-sentiment
.venv/bin/python -m src.cli run --year 2024 --all --with-deep-sentiment --with-parent-company-deep-sentiment
```

Run all available workflows (pipeline + sentiment + deep sentiment + grouping + maps + breakdowns):

```bash
.venv/bin/python -m src.cli run-everything --year 2024
```

Run everything except selected workflows (repeat `--exclude`):

```bash
.venv/bin/python -m src.cli run-everything --year 2024 --exclude deep-sentiment --exclude group-parent-companies
```

Valid excludes: `sentiment`, `ad-sentiment`, `deep-sentiment`, `parent-company-sentiment`,
`parent-company-deep-sentiment`, `group-brands`, `group-parent-companies`,
`sentiment-maps`, `emotion-breakdowns`.
Notes: `ad-sentiment` requires `sentiment`, and `parent-company-deep-sentiment` requires
`deep-sentiment` (these two combinations are hard errors if excluded).

## Stages

- ingest: schema validation from `data/raw/<year>/` to `data/processed/<year>/ingested.csv`
- clean: dedupe/null/timestamp normalization to `data/processed/<year>/cleaned.csv`
  (includes canonical Twitter fields such as `id`, `author_id`, `conversation_id`,
  `entities.*`, `public_metrics.*`, `username`, and `name`; adds `pipeline_row_id`)
- process: text features/tags to `data/enriched/<year>/enriched.csv`
- analyze: analytics artifact generation under `outputs/analytics/<year>/`
- sentiment (optional): BERTweet sentiment inference → `sentiment/bertweet/<year>/sentiment.json`
- ad_sentiment (optional): joins sentiment + enriched rows → ad-level outputs
- deep_sentiment (optional): deep emotion inference → `sentiment/deep/<year>/deep_sentiment.json`
- parent_company_sentiment (optional): joins sentiment + parent company groupings
- parent_company_deep_sentiment (optional): joins deep sentiment + parent company groupings
- visualize (optional): placeholder visualization output
- export (optional): placeholder export artifact

## LLM Grouping Workflows

Brand-grouping (hashtags → brands):

```bash
cp .env.example .env
export OPENROUTER_API_KEY=... # keep local only; never commit
.venv/bin/python -m src.cli group-brands --year 2024 --model openai/gpt-4.1-mini
```

Parent-company grouping (brands → parent companies):

```bash
.venv/bin/python -m src.cli group-parent-companies --year 2024 --model openai/gpt-4.1-mini
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

Deep sentiment (Twitter-trained model):

```bash
.venv/bin/python -m src.cli deep-sentiment --year 2024 --batch-size 64
```

GPU usage:
- Defaults to CUDA if available (falls back to CPU).
- Override with `--device cpu` for the CLI, or `--sentiment-device` / `--deep-sentiment-device` for `run`.

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

```bash
.venv/bin/python -m src.scripts.emotion_breakdown \
  --input-jsonl outputs/aux/2024/deep_sentiment_company_map.jsonl \
  --parent-out outputs/aux/2024/parent_company_emotion_breakdown.json \
  --brand-out outputs/aux/2024/brand_emotion_breakdown.json
```

Reclassify sentiment by confidence (keep both datasets):

```bash
.venv/bin/python -m src.scripts.reclassify_sentiment_by_confidence \
  --input-file sentiment/bertweet/2024/sentiment.json \
  --output-file sentiment/bertweet/2024/sentiment_reclassified.json \
  --threshold 0.65 \
  --label-field sentiment
```

```bash
.venv/bin/python -m src.scripts.reclassify_sentiment_by_confidence \
  --input-file sentiment/deep/2024/deep_sentiment.json \
  --output-file sentiment/deep/2024/deep_sentiment_reclassified.json \
  --threshold 0.65 \
  --label-field main_sentiment
```

Other helper scripts:
- `src/scripts/split_raw_csv.py` (first N rows of raw data)
- `src/scripts/split_cleaned_csv.py` (first N rows of cleaned data)
- `src/scripts/split_hashtags_frequency.py` (first N hashtags for grouping)
- `src/scripts/recover_grouping_from_partial.py` (rebuild groups from partial JSONL)

## Visualization Website

The `site/` folder contains a React + ECharts visualization dashboard.

Quickstart:

```bash
cd site
npm install
npm run dev
```

The site reads artifacts from:
- `outputs/analytics/<year>/`
- `outputs/aux/<year>/`

Optional: add `outputs/analytics/index.json` with a `years` array for year picker defaults.

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
              +--> sentiment/deep/deep_sentiment.json (pipeline_row_id)
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
- `parent_company_deep_sentiment_summary.json`
- `parent_company_deep_sentiment_summary.csv`
- `parent_company_deep_sentiment_timeslices.json`
- `parent_company_deep_sentiment_timeslices.csv`

Auxiliary outputs (`outputs/aux/<year>/`, gitignored):
- `brand_tweet_map.json`
- `parent_company_tweet_map.json`
- `*_partial.jsonl`
- `*_parse_failures.txt`
- `*_recovered.json`
- `parent_company_deep_sentiment_joined.parquet`
- `sentiment_company_map.jsonl`
- `deep_sentiment_company_map.jsonl`
- `parent_company_tweet_map.jsonl`
- `*_emotion_breakdown.json`

Sentiment outputs:
- `sentiment/bertweet/<year>/sentiment.json`
- `sentiment/bertweet/<year>/sentiment_reclassified.json`
- `sentiment/deep/<year>/deep_sentiment.json`
- `sentiment/deep/<year>/deep_sentiment_reclassified.json`

## Models

BERTweet sentiment:
- Default: `finiteautomata/bertweet-base-sentiment-analysis`
- Fallback (explicit): `rabindralamsal/finetuned-bertweet-sentiment-analysis`

Deep sentiment (Twitter-trained):
- Default: `cardiffnlp/twitter-roberta-base-emotion-latest`
- Native labels are preserved (no fixed taxonomy).

## Notes

- Sentiment confidence gate: deep sentiment outputs are reclassified to `neutral` when confidence < 0.65.
- `run-everything` assumes `OPENROUTER_API_KEY` is set for grouping workflows.
- `--data-dir` is treated as the explicit raw-input directory for that run (it is not rewritten).
