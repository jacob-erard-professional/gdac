# Twitter (X) Data Cleaning Pipeline

## Purpose

This repository cleans, normalizes, and validates messy Twitter (X) data for
clean downstream consumption. It focuses on tweets with a guessed `brand`
association and a `text` field. The pipeline is deterministic, step-based, and
fully auditable. It does not train models or perform analytics.

## What This Repository Does Not Do

- Train machine learning models
- Perform sentiment or emotion analysis
- Perform aggregation or reporting
- Make irreversible assumptions about brand correctness

## Repository Layout

```text
data/
  raw/           # Original input CSVs (read-only)
  intermediate/  # Outputs of individual cleaning steps
  clean/         # Final cleaned datasets
src/
  ingest/        # Schema validation and loading logic
  cleaning/      # One module per cleaning step
  brand/         # Brand validation, normalization, and relevance logic
  text/          # Text normalization, deduplication, and filtering logic
  orchestrator/  # Pipeline runner and step coordination
  config/        # YAML or JSON configs controlling pipeline behavior
scripts/         # CLI entry points only (no business logic)
```

## Pipeline Steps

Each cleaning concern is implemented as its own step. Steps are independently
runnable and composable into a full pipeline. Brand relevance classification is
performed by stateless LLM agents routed through the OpenRouter API.

1. Schema Validation
2. Text Normalization
3. Noise Handling
4. Brand Normalization
5. Brand Relevance Validation (OpenRouter-backed agents)

Each step:
- Reads from exactly one input directory
- Writes to exactly one output directory
- Produces a manifest with input/output hashes, row counts, and rejection reasons
- Logs structured, machine-readable row counts and rejection details

## Schemas

All datasets must adhere to explicit schemas:
- `text` (string, non-empty)
- `brand` (string, may be empty or incorrect)

Rows that violate schema requirements are logged, counted, and either corrected
explicitly or quarantined.

## Running the Pipeline

Planned CLI usage (to be implemented by `scripts/` entry points):

```bash
# Run full pipeline for a year
python -m scripts.pipeline run \
  --config src/config/pipeline.yaml \
  --year 2023

# Run a single step for a year
python -m scripts.pipeline step \
  --name text_normalization \
  --config src/config/pipeline.yaml \
  --year 2023

# Validation-only / dry-run
python -m scripts.pipeline validate \
  --config src/config/pipeline.yaml \
  --year 2023
```

## Tests

Run the unit tests with:

```bash
pytest
```

CLI entry points live in `scripts/` and must not contain business logic.

## Configuration

All thresholds, heuristics, and toggles live in configuration files under
`src/config/`. Defaults must be documented in those files. OpenRouter model
selection and parameters are configured here, and agent prompts are versioned.

Key config files:
- `src/config/pipeline.yaml` for paths and step configuration
- `src/config/column_registry.yaml` for column registry and schema versioning
- `src/config/brand_aliases.yaml` for brand alias mappings
- `src/config/openrouter.schema.json` for OpenRouter config contract

Model swap instructions:
1. Update `openrouter.model` (and optional `openrouter.models`) in `src/config/pipeline.yaml`.
2. Keep model parameters in `openrouter.model_params` to avoid code changes.
3. Re-run the pipeline; outputs are cached by input hash and prompt version.

## Determinism and Auditability

Given the same input data and configuration, the pipeline always produces the
same outputs. Any step that depends on ordering must define a stable ordering.
Raw input data is never mutated or overwritten. Agent inputs are hashed and
outputs are cached to ensure re-playable results.

## Derived Columns Contract

Derived columns added by the pipeline include (non-exhaustive):
- `text_original`, `text_normalized`, `url_handling_applied`
- `brand_original`, `brand_normalized`, `brand_relevant`, `brand_confidence`, `brand_rationale`
- `brand_empty`, `brand_unknown`, `brand_alias_resolved`, `brand_known`
- `is_retweet`, `is_duplicate`

All other Twitter-provided columns are preserved and passed through unmodified.

## Year-Based I/O

Inputs are read from `data/raw/<year>/` and outputs are written to
`outputs/<year>/`. Intermediate artifacts live under
`data/intermediate/<year>/`.

## Contributing

- New features or cleaning steps must update this README, including how to run
  the new or updated feature.
- No silent data changes: schema violations must be logged, counted, and handled
  explicitly.
