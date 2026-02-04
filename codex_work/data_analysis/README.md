# Super Bowl Twitter Data Analysis

This repository contains a deterministic, stage-based CLI pipeline for year-scoped
Twitter Super Bowl analysis.

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

Full pipeline from explicit data directory:

```bash
.venv/bin/python -m src.cli run --data-dir data/raw/2024 --all
```

Full pipeline for all discovered years under `data/raw/`:

```bash
.venv/bin/python -m src.cli run --all
```

`--data-dir` is treated as the explicit raw-input directory for that run (it is not rewritten).

Brand-grouping agent workflow (reads `hashtags_frequency.json` and groups hashtag aliases by brand):

```bash
cp .env.example .env
export OPENROUTER_API_KEY=... # keep local only; never commit
.venv/bin/python -m src.cli group-brands --year 2023 --model openai/gpt-oss-120b:free
```

If free-model rate limits are high, add `--request-delay 2.5 --max-rate-limit-retries 12`.

Parent-company grouping agent workflow (reads `brand_groups.json` and groups brands under parent companies):

```bash
.venv/bin/python -m src.cli group-parent-companies --year 2023 --model openai/gpt-oss-120b:free
```

## Stages

- ingest: schema validation from `data/raw/<year>/` to `data/processed/<year>/ingested.csv`
- clean: dedupe/null/timestamp normalization to `data/processed/<year>/cleaned.csv`
  (includes canonical Twitter fields such as `id`, `author_id`, `conversation_id`,
  `entities.*`, `public_metrics.*`, `username`, and `name`)
- process: text features/tags to `data/enriched/<year>/enriched.csv`
- analyze: analytics artifact generation under `outputs/analytics/<year>/`
- visualize (optional): placeholder visualization output
- export (optional): placeholder export artifact

## Analytics Capabilities

- Hashtag frequency list ordered by frequency (`hashtags_frequency.json`)
- Mention frequency list ordered by frequency (`mentions_frequency.json`)

## Outputs and Metadata

The analyze stage writes only two files under `outputs/analytics/<year>/`:
`hashtags_frequency.json` and `mentions_frequency.json`.

The brand-grouping agent writes:
- `outputs/analytics/<year>/brand_groups.json`

The parent-company grouping agent writes:
- `outputs/analytics/<year>/parent_company_groups.json`
