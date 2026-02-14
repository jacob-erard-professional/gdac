# Quickstart: Brand List Classifier

## Prerequisites

- Python 3.11
- OpenRouter API key exported as `OPENROUTER_API_KEY`
- Tweet CSV with `text` and `is_about_brand`
- Brand CSV with one header column: `brand`

## Run

```bash
export OPENROUTER_API_KEY="your_api_key"
python3 -m src.cli.classify_brand_list \
  --input data/input/tweets.csv \
  --brand-list data/input/brands.csv \
  --output data/output/brand_list_classified.csv \
  --model openrouter/your-model \
  --batch-size 100 \
  --progress-every 1
```

## Behavior

- Rows with true-like `is_about_brand` remain in output and are marked:
  - `category=skipped`
  - `assigned_brand=""`
  - `suggested_brand=""`
  - `confidence=0`
  - `rationale="Skipped: already is_about_brand=true"`
- Candidate rows are classified as one of: `listed_brand`, `new_brand`, `no_brand`.

## Output Fields

- `category`
- `assigned_brand`
- `suggested_brand`
- `confidence`
- `rationale`

## Notes

- Reuses OpenRouter request and CSV handling patterns from existing workflow.
- Update `README.md` alongside implementation changes.
