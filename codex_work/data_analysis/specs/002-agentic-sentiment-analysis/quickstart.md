# Quickstart: Agentic Sentiment Analysis for X (Twitter) Data

## Preconditions

1. Upstream cleaned dataset exists for a target year.
2. `OPENROUTER_API_KEY` is set in the environment.
3. Baseline pipeline artifacts remain unchanged by default.

## CLI Run Examples

Run sentiment for one year:

```bash
python -m src.cli sentiment --year 2024
```

Run sentiment from explicit input directory:

```bash
python -m src.cli sentiment --data-dir data/raw/2024
```

Run with debug logs and dry-run validation:

```bash
python -m src.cli sentiment --year 2024 --dry-run --verbose
```

Run full pipeline with optional sentiment step:

```bash
python -m src.cli run --year 2024 --all --with-sentiment
```

## Expected Outputs

- `outputs/analytics/<year>/sentiment_agentic.jsonl`
- `outputs/analytics/<year>/sentiment_agentic_summary.json`

## Validation Checklist

- Determinism: same input + config yields structurally consistent records.
- Schema safety: all agent outputs pass strict JSON validation.
- Year isolation: no cross-year overwrite.
- Raw immutability: no writes to `data/raw/`.
- Backward compatibility: baseline analytics unchanged without sentiment flag.
