# Quickstart: Deterministic Twitter (X) Data Cleaning + OpenRouter Agents

## Prerequisites

- Python 3.11
- OpenRouter API key available in environment (configured via `api_key_env`)
- Input CSVs placed in `data/raw/`

## Configuration

Create a config file under `src/config/` (YAML or JSON) that defines:
- Pipeline steps and directories
- Normalization rules
- OpenRouter model configuration (model id, parameters, retries, timeout)

## Planned CLI Usage

These commands define the target CLI interface to implement:

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

## Outputs

- `data/intermediate/<step>/` contains step outputs
- `data/clean/` contains final outputs
- Each step emits a manifest with hashes and row counts
- Structured logs are emitted for rows in/out and rejections
