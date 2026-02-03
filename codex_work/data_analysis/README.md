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
  analytics/<year>/
```

Raw files are immutable after ingest.

## CLI

Single stage:

```bash
python -m src.cli run --year 2024 --stage clean
```

Full pipeline for one year:

```bash
python -m src.cli run --year 2024 --all
```

Full pipeline from explicit data directory:

```bash
python -m src.cli run --data-dir data/raw/2024 --all
```

## Stages

- ingest: schema validation from `data/raw/<year>/` to `data/processed/<year>/ingested.csv`
- clean: dedupe/null/timestamp normalization to `data/processed/<year>/cleaned.csv`
- process: text features/tags to `data/enriched/<year>/enriched.csv`
- analyze: analytics artifact generation under `data/analytics/<year>/`
- visualize (optional): placeholder visualization output
- export (optional): placeholder export artifact

## Analytics Capabilities

- Brand/ad volume metrics
- Sentiment aggregation
- Time-bucket analysis
- ROI proxy metrics
- Relationship analysis
- Event-aligned analysis
- Text/network hashtag co-occurrence summary

## Outputs and Metadata

Each stage emits a manifest JSON under `data/analytics/<year>/` with input files,
output files, timestamps, and record counts.
