# GDAC Repository Overview

This repository contains two complementary Python projects:

- `codex_work/data_cleaning`: LLM-assisted dataset cleaning and label refinement
- `codex_work/data_analysis`: deterministic analytics pipeline + optional sentiment/grouping workflows

The typical lifecycle is:
1. Clean/verify tweet-brand labels in `data_cleaning`.
2. Run year-scoped analytics and optional enrichment in `data_analysis`.

## Project Map

| Area | Primary Goal | Main Entry Points | Core Output Shape |
|---|---|---|---|
| `codex_work/data_cleaning` | Decide whether tweets are actually about assigned brands; optionally assign brands from a candidate list | `src/cli/classify_brand_mentions.py`, `src/cli/classify_brand_list.py` | Classified CSV/JSONL with `is_about_brand`, `confidence`, `rationale`, plus brand-list fields |
| `codex_work/data_analysis` | Run ingest/clean/process/analyze stages over yearly datasets, then optional sentiment + LLM grouping workflows | `src/cli/main.py`, `src/cli/run.py`, `src/cli/run_everything.py` | Year-partitioned artifacts under `data/processed/`, `data/enriched/`, `outputs/analytics/`, `outputs/aux/`, `sentiment/bertweet/` |

## `data_cleaning` In-Depth

### What it does

`data_cleaning` focuses on row-level quality control before downstream analytics:

1. Reads input CSV rows.
2. Builds LLM prompts from tweet text and context.
3. Calls OpenRouter with JSON schema constraints.
4. Parses/normalizes responses.
5. Writes merged results as CSV or JSONL.

It includes two classifiers:
- Brand mention classifier (`is_about_brand`)
- Brand-list classifier (`listed_brand` / `new_brand` / `no_brand`)

### How it runs internally

Brand mention flow:
- CLI argument parsing and batching: `codex_work/data_cleaning/src/cli/classify_brand_mentions.py`
- Prompting + schema call + parse: `codex_work/data_cleaning/src/lib/classifier.py`
- Prompt construction: `codex_work/data_cleaning/src/lib/prompt_builder.py`
- Response parsing/validation: `codex_work/data_cleaning/src/lib/response_parser.py`

Brand-list flow:
- CLI orchestration: `codex_work/data_cleaning/src/cli/classify_brand_list.py`
- Category normalization and merge rules: `codex_work/data_cleaning/src/lib/brand_list_classifier.py`

### Where to learn more (`data_cleaning`)

- Operational usage and examples: `codex_work/data_cleaning/README.md`
- Spec-driven quickstart and behavior contract: `codex_work/data_cleaning/specs/001-brand-mention-classifier/quickstart.md`
- Feature scope/design docs:
  - `codex_work/data_cleaning/specs/001-brand-mention-classifier/spec.md`
  - `codex_work/data_cleaning/specs/002-brand-list-classifier/spec.md`
- Expected behavior via tests:
  - `codex_work/data_cleaning/tests/unit/`
  - `codex_work/data_cleaning/tests/integration/`

## `data_analysis` In-Depth

### What it does

`data_analysis` is a deterministic, stage-based pipeline for year-scoped Super Bowl Twitter datasets.  
Core stage sequence:

1. `ingest`
2. `clean`
3. `process`
4. `analyze`

Optional extensions:
- `sentiment` (BERTweet)
- `ad_sentiment`
- `parent_company_sentiment`
- `agentic_emotion`
- LLM grouping workflows (`group-brands`, `group-parent-companies`)
- helper mapping/breakdown scripts under `src/scripts/`

### How it runs internally

Command routing:
- Typer CLI command registration: `codex_work/data_analysis/src/cli/main.py`
- Pipeline run command (`--stage` / `--all`): `codex_work/data_analysis/src/cli/run.py`
- End-to-end orchestrated workflow: `codex_work/data_analysis/src/cli/run_everything.py`

Pipeline orchestration:
- Mode/year resolution + per-stage execution loop: `codex_work/data_analysis/src/pipeline/orchestrator.py`
- Stage ordering: `codex_work/data_analysis/src/pipeline/stage_registry.py`
- Path/year config resolution: `codex_work/data_analysis/src/pipeline/path_resolution.py`
- Runtime request model: `codex_work/data_analysis/src/pipeline/config.py`

Stage implementations:
- `codex_work/data_analysis/src/pipeline/stages/ingest.py`
- `codex_work/data_analysis/src/pipeline/stages/clean.py`
- `codex_work/data_analysis/src/pipeline/stages/process.py`
- `codex_work/data_analysis/src/pipeline/stages/analyze.py`
- optional stages in the same folder (`sentiment.py`, `ad_sentiment.py`, `parent_company_sentiment.py`, `agentic_emotion.py`)

### Where to learn more (`data_analysis`)

- Full command reference and artifact layout: `codex_work/data_analysis/README.md`
- Baseline pipeline quickstart: `codex_work/data_analysis/specs/001-build-superbowl-analytics-pipeline/quickstart.md`
- Detailed feature specs (sentiment, viz, grouping, agentic emotion): `codex_work/data_analysis/specs/`
- Execution guarantees and contracts via tests:
  - `codex_work/data_analysis/tests/integration/`
  - `codex_work/data_analysis/tests/unit/`

## Recommended Learning Path

1. Read `codex_work/data_cleaning/README.md` and run one classifier command.
2. Read `codex_work/data_analysis/README.md` and run `src.cli run --year <year> --all`.
3. Open `codex_work/data_analysis/src/pipeline/orchestrator.py` to understand exact stage execution.
4. Use integration tests in both projects to verify assumptions before modifying workflows.
