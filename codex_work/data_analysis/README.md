# Super Bowl Twitter Data Analysis

This repository cleans, processes, and analyzes large-scale Super Bowl Twitter CSV
datasets with deterministic, year-scoped pipeline runs.

## Required Data Layout

```text
data/
  raw/<year>/*.csv
  processed/<year>/
  enriched/<year>/
  analytics/<year>/
```

`data/raw` is read-only after ingest.

## Pipeline Stages

- `ingest`
- `clean`
- `process`
- `analyze`
- `visualize` (optional)
- `export`

Each stage must support explicit input/output paths and independent CLI execution.

## Run Modes (Conceptual)

- Single stage, single year: `run --year 2024 --stage clean`
- Full pipeline, single year: `run --year 2024 --all`
- Full pipeline, explicit directory: `run --data-dir data/raw/2023 --all`

## Analytics Scope

- Brand and ad volume metrics
- Sentiment by ad/brand over time
- Quarter/minute and before/after analysis
- ROI proxy metrics (cost, followers, retweets, engagement)
- Variable relationship analysis
- Event-aligned analysis (game events, ad timing)
- Text mining and co-occurrence/network analysis

## Governance

Repository governance is defined in `.specify/memory/constitution.md`.
