# Quickstart: Super Bowl X Analytics Pipeline

## Prerequisites

- Python 3.12 installed
- Project dependencies installed
- For ML emotion modeling: install `nltk` and `torch` (otherwise lexicon fallback is used)
- Input data available under `data/raw/<event>/<year>/`
- Config files prepared for event windows, keywords, and KPI definitions

For large CSV datasets (GB scale), set `input_format: csv` and `chunk_size` in
`config/pipeline.yaml` so ingestion runs in streaming chunks.

## 1) Configure run inputs

Create/update config files:

- `config/event_windows.yaml`
- `config/keywords.yaml`
- `config/kpi_definitions.yaml`

Ensure event and year keys exist for target run.

CSV-specific config keys (for large files):

- `input_format: csv`
- `chunk_size: 100000` (adjust by memory budget)
- `csv_delimiter`, `csv_encoding`
- `csv_columns` mappings for `source_record_id`, `event_name`, `year`, `text`

## 2) Run a single year

```bash
python -m src.orchestrator.run_pipeline --event super-bowl --year 2025 --config config/pipeline.yaml
```

Expected outputs:

- `outputs/super-bowl/2025/kpis/`
- `outputs/super-bowl/2025/kpis/hashtag_frequencies.jsonl`
- `outputs/super-bowl/2025/kpis/mention_frequencies.jsonl`
- `outputs/super-bowl/2025/kpis/nlp_lexicon/emotion_by_ad.jsonl`
- `outputs/super-bowl/2025/kpis/nlp_lexicon/similar_hashtags.jsonl`
- `outputs/super-bowl/2025/kpis/nlp_lexicon/emotion_overview.json`
- `outputs/super-bowl/2025/kpis/nlp_ml/emotion_by_ad.jsonl`
- `outputs/super-bowl/2025/kpis/nlp_ml/similar_hashtags.jsonl`
- `outputs/super-bowl/2025/kpis/nlp_ml/emotion_overview.json`
- `outputs/super-bowl/2025/kpis/brand_popularity.jsonl`
- `outputs/super-bowl/2025/kpis/roi_join_ready.csv`
- `outputs/super-bowl/2025/visuals/`
- `outputs/super-bowl/2025/summaries/`
- `outputs/super-bowl/2025/manifests/`

## 3) Run additional years for comparison

```bash
python -m src.orchestrator.run_pipeline --event super-bowl --year 2024 --config config/pipeline.yaml
python -m src.orchestrator.run_pipeline --event super-bowl --year 2023 --config config/pipeline.yaml
```

## 4) Validate reproducibility

Re-run one prior year with unchanged config and compare KPI outputs/checksums:

```bash
python -m src.orchestrator.run_pipeline --event super-bowl --year 2025 --config config/pipeline.yaml
```

Pass condition:

- KPI values are consistent for unchanged source/config inputs.
- Manifest references identical config and KPI definition versions.

## 5) Review data quality and reporting artifacts

- Check stage logs for validation and rejection summaries.
- Confirm white paper and executive summaries include assumptions and limitations.
- Confirm artifacts include year metadata for cross-year comparison.
- Review `hashtag_frequencies.jsonl` and `mention_frequencies.jsonl` for frequent
  topics and tagged accounts.
- Review both NLP tracks (`nlp_lexicon` and `nlp_ml`) for ad-level emotion distribution using:
  Joy, Excitement, Anger, Disappointment, Surprise, Disgust, and Pride.
- Review `brand_popularity.jsonl` for top brands by retweets, likes, and total
  interaction (with typo alias grouping).
- Use `roi_join_ready.csv` to merge ad emotion outputs with spend/ROI metrics.
- Check run logs for `ml_mode=ml_torch_nltk` to confirm ML classification is active.

## 6) Validate CLI contract outputs (MVP)

- Validate `outputs/<event>/<year>/manifests/run_manifest.json` includes `run_id`,
  `config_hash`, and `artifact_index`.
- Validate `outputs/<event>/<year>/manifests/artifact_index.json` entries include
  `artifact_type`, `year`, `file_path`, and checksum.
- Contract coverage is implemented as logical schema validation in test files, not as a
  deployed HTTP service requirement for MVP.

## 7) Run test suite

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```
