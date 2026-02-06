# Super Bowl Twitter Data Analysis

This repository contains a deterministic, stage-based CLI pipeline for year-scoped
Twitter Super Bowl analysis.

Beyond the deterministic pipeline, there are LLM calls that group together similar hashtags.

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
```

Raw files are immutable after ingest.

## CLI

Single stage:

```bash
.venv/bin/python -m src.cli run --year 2024 --stage clean
```

Full pipeline for one year:

```bash
.venv/bin/python -m src.cli run --year 2024 --all
```

Full pipeline with optional BERTweet sentiment inference:

```bash
.venv/bin/python -m src.cli run --year 2024 --all --with-sentiment
```

Full pipeline with sentiment + ad sentiment aggregation:

```bash
.venv/bin/python -m src.cli run --year 2024 --all --with-sentiment --with-ad-sentiment
```

Full pipeline with optional deeper emotion classification:

```bash
.venv/bin/python -m src.cli run --year 2024 --all --with-deep-sentiment
```

Full pipeline with parent-company sentiment impact:

```bash
.venv/bin/python -m src.cli run --year 2024 --all --with-sentiment --with-parent-company-sentiment
```

Full pipeline with parent-company deep sentiment impact:

```bash
.venv/bin/python -m src.cli run --year 2024 --all --with-deep-sentiment --with-parent-company-deep-sentiment
```

Full pipeline from explicit data directory:

```bash
.venv/bin/python -m src.cli run --data-dir data/raw/2024 --all
```

Full pipeline for all discovered years under `data/raw/`:

```bash
.venv/bin/python -m src.cli run --all
```

`--data-dir` is treated as the explicit raw-input directory for that run (it is not rewritten).

Run all available workflows for one year (pipeline + sentiment + deep sentiment + grouping):

```bash
.venv/bin/python -m src.cli run-everything --year 2024
```

Run everything except selected workflows (repeat `--exclude` as needed):

```bash
.venv/bin/python -m src.cli run-everything --year 2024 --exclude deep-sentiment --exclude group-parent-companies
```

`run-everything` assumes `OPENROUTER_API_KEY` is already set when grouping workflows are included.
Valid excludes: `sentiment`, `ad-sentiment`, `deep-sentiment`, `parent-company-deep-sentiment`, `group-brands`, `group-parent-companies`.

Brand-grouping agent workflow (reads `hashtags_frequency.json` and groups hashtag aliases by brand):

```bash
cp .env.example .env
export OPENROUTER_API_KEY=... # keep local only; never commit
.venv/bin/python -m src.cli group-brands --year 2023 --model openai/gpt-oss-120b:free
```

If free-model rate limits are high, add `--request-delay 2.5 --max-rate-limit-retries 12`.
All agentic workflows enforce constitution-aligned minimum throttling and retries
(currently 2.5s request delay and 12 rate-limit retries), even if lower values are passed.

Parent-company grouping agent workflow (reads `brand_groups.json` and groups brands under parent companies):

```bash
.venv/bin/python -m src.cli group-parent-companies --year 2023 --model openai/gpt-oss-120b:free
```

Parent-company grouping applies deterministic franchise/company overrides from
`config/parent_company_overrides.json` before LLM mapping (for example, minions
and despicableme4 map to universal).

BERTweet sentiment workflow (independent CLI command):

```bash
.venv/bin/python -m src.cli sentiment --year 2024 --batch-size 64
```

Deep sentiment workflow (independent CLI command):

```bash
.venv/bin/python -m src.cli deep-sentiment --year 2024 --batch-size 64
```

Ad-level sentiment aggregation workflow:

```bash
.venv/bin/python -m src.cli ad-sentiment --year 2024
```

Parent-company sentiment impact workflow:

```bash
.venv/bin/python -m src.cli parent-company-sentiment --year 2024
```

Parent-company deep sentiment impact workflow:

```bash
.venv/bin/python -m src.cli parent-company-deep-sentiment --year 2024
```

Run sentiment on a custom dataset:

```bash
.venv/bin/python -m src.cli sentiment --input-file /path/to/my_dataset.parquet --year 2024
```

The default model is `finiteautomata/bertweet-base-sentiment-analysis`.
Fallback model use is disabled by default to avoid silent substitution. To allow
the explicit fallback (`rabindralamsal/finetuned-bertweet-sentiment-analysis`),
pass `--allow-fallback`.

## Stages

- ingest: schema validation from `data/raw/<year>/` to `data/processed/<year>/ingested.csv`
- clean: dedupe/null/timestamp normalization to `data/processed/<year>/cleaned.csv`
  (includes canonical Twitter fields such as `id`, `author_id`, `conversation_id`,
  `entities.*`, `public_metrics.*`, `username`, and `name`)
- process: text features/tags to `data/enriched/<year>/enriched.csv`
- analyze: analytics artifact generation under `outputs/analytics/<year>/`
- sentiment (optional): deterministic BERTweet sentiment inference written to `sentiment/bertweet/<year>/sentiment.json`
- ad_sentiment (optional): joins sentiment + enriched rows and writes ad-level sentiment outputs
- deep_sentiment (optional): deterministic deep emotion inference written to `sentiment/deep/<year>/deep_sentiment.json`
- parent_company_sentiment (optional): joins sentiment + parent company groupings and writes company impact outputs
- parent_company_deep_sentiment (optional): joins deep sentiment + parent company groupings and writes emotion impact outputs
- visualize (optional): placeholder visualization output
- export (optional): placeholder export artifact

## Analytics Capabilities

- Hashtag frequency list ordered by frequency (`hashtags_frequency.json`)
- Mention frequency list ordered by frequency (`mentions_frequency.json`)

## Outputs and Metadata

The analyze stage writes only two files under `outputs/analytics/<year>/`:
`hashtags_frequency.json` and `mentions_frequency.json`.

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

The brand-grouping agent writes:
- `outputs/analytics/<year>/brand_groups.json`
- `outputs/analytics/<year>/brand_tweet_map.json`

The parent-company grouping agent writes:
- `outputs/analytics/<year>/parent_company_groups.json`
- `outputs/analytics/<year>/parent_company_tweet_map.json`

The BERTweet sentiment workflow writes:
- `sentiment/bertweet/<year>/sentiment.json`

The ad sentiment workflow writes:
- `outputs/analytics/<year>/ad_sentiment_joined.parquet`
- `outputs/analytics/<year>/ad_sentiment_summary.json`
- `outputs/analytics/<year>/ad_sentiment_summary.csv`

The parent-company sentiment workflow writes:
- `outputs/analytics/<year>/parent_company_sentiment_joined.parquet`
- `outputs/analytics/<year>/parent_company_sentiment_summary.json`
- `outputs/analytics/<year>/parent_company_sentiment_summary.csv`
- `outputs/analytics/<year>/parent_company_sentiment_timeslices.json`
- `outputs/analytics/<year>/parent_company_sentiment_timeslices.csv`
- `outputs/analytics/<year>/parent_company_sentiment_by_ad_tag.json`
- `outputs/analytics/<year>/parent_company_sentiment_by_ad_tag.csv`

The deep sentiment workflow writes:
- `sentiment/deep/<year>/deep_sentiment.json`

The parent-company deep sentiment workflow writes:
- `outputs/analytics/<year>/parent_company_deep_sentiment_joined.parquet`
- `outputs/analytics/<year>/parent_company_deep_sentiment_summary.json`
- `outputs/analytics/<year>/parent_company_deep_sentiment_summary.csv`
- `outputs/analytics/<year>/parent_company_deep_sentiment_timeslices.json`
- `outputs/analytics/<year>/parent_company_deep_sentiment_timeslices.csv`

## BERTweet Sentiment Notes

- Why BERTweet: the default checkpoint is pretrained for tweet text and already includes a sentiment classification head.
- Preprocessing: URLs are removed and whitespace normalized; hashtags/emojis/punctuation are preserved.
- Output interpretation: each record contains `tweet_id`, `year`, `text`, `sentiment`, and model confidence.
- GPU usage: defaults to CUDA when available; falls back to CPU if not (`--device cpu` to force).
- Known limitations: sarcasm, memes, and domain drift can reduce accuracy; model outputs may reflect dataset bias.

## Deep Sentiment Notes

- Why this model: default `SamLowe/roberta-base-go_emotions` offers broad emotion coverage and can be canonically mapped to required labels.
- Required taxonomy: `joy`, `surprise`, `anger`, `disappointment`, `excitement`, `neutral`.
- Output interpretation: each record contains `tweet_id`, `hashtags`, `text`, `main_sentiment`, `year`, and confidence.
- Label mapping: provide `--label-map-file path/to/map.json` when using a custom model with non-standard label names.
- GPU usage: defaults to CUDA when available; falls back to CPU if not (`--device cpu` to force).
- Known limitations: nuanced emotions can collapse into required categories and may not capture sarcasm or mixed sentiment.
