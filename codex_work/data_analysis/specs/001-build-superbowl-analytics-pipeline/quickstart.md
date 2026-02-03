# Quickstart: Twitter Super Bowl Analytics Pipeline

## Preconditions

1. Place raw CSV inputs under `data/raw/<year>/`.
2. Do not edit files in `data/raw/` after ingest.
3. Ensure destination year folders exist or are creatable in:
   - `data/processed/<year>/`
   - `data/enriched/<year>/`
   - `outputs/analytics/<year>/`

## CLI Run Examples

Single stage, single year:

```bash
python -m src.cli run --year 2024 --stage clean
```

Full pipeline, single year:

```bash
python -m src.cli run --year 2024 --all
```

Full pipeline from explicit data directory:

```bash
python -m src.cli run --data-dir data/raw/2023 --all
```

Full pipeline for all discovered years:

```bash
python -m src.cli run --all
```

Note: `--data-dir` is used as the explicit raw input directory for the run.

## Expected Outputs

A successful full run produces:

- processed artifacts in `data/processed/<year>/`
- enriched artifacts in `data/enriched/<year>/`
- analytics artifacts in `outputs/analytics/<year>/`
- stage manifests with input/output/count metadata per stage

## Validation Checklist

- Determinism: identical input + command => identical outputs
- Raw immutability: no writes under `data/raw/`
- Stage isolation: each stage callable independently
- Year isolation: no output overwrite across years
- README update: required if commands/stages/modules change
