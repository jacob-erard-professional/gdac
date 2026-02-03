# Modular, Resumable, Agentic NLP Pipeline

This repository provides a CLI-first NLP analytics pipeline with independently runnable stages:

- `ingest`
- `clean`
- `enrich`
- `normalize-hashtags`
- `emotion-lexicon` (optional, slower)
- `emotion-ml` (optional, slowest)
- `analyze`

## MVP Features

- Explicit stage execution with `--input`, `--output`, `--config`, `--dry-run`
- Repeatable yearly datasets under `data/<event>/<year>/file.csv` via `--event` and `--year`
- Subset runs without implicit upstream execution
- Skip-completed logic based on manifest status and output artifacts
- Manifest lineage tracking for runs and artifacts
- Run records include `event` and `year` context for season-by-season traceability
- Agentic hashtag normalization with confidence-scored mappings and metadata
- Dual emotion classification outputs (lexicon + machine learning) for tweet-level sentiment analytics

## Quickstart

```bash
pipeline stage run ingest --event superbowl --year 2024 --output artifacts/ingest/posts.v1.jsonl --config configs/ingest.yaml
pipeline stage run clean --input artifacts/ingest/posts.v1.jsonl --output artifacts/clean/posts.v1.jsonl --config configs/clean.yaml
pipeline stage run enrich --input artifacts/clean/posts.v1.jsonl --output artifacts/enrich/hashtags.v1.json --config configs/enrich.yaml
pipeline stage run normalize-hashtags --input artifacts/enrich/hashtags.v1.json --output artifacts/hashtag_normalization/mappings.v1.json --config configs/normalize_hashtags.yaml
pipeline stage run emotion-lexicon --input artifacts/clean/posts.v1.jsonl --output artifacts/emotion_lexicon/predictions.v1.json --config configs/emotion_lexicon.yaml
pipeline stage run emotion-ml --input artifacts/clean/posts.v1.jsonl --output artifacts/emotion_ml/predictions.v1.json --config configs/emotion_ml.yaml
pipeline stage run analyze --input artifacts/enrich/hashtags.v1.json --output artifacts/analyze/report.v1.json --config configs/analyze.yaml
```

Emotion stages classify each tweet into:
`joy`, `surprise`, `anger`, `disgust`, `excitement`, `disappointment`, `humorous`.
They only execute when explicitly invoked, and each requires `enabled: true` in its config.

## OpenRouter Setup for Agentic Hashtag Matching

1. Copy `.env.openrouter.example` to `.env.openrouter`.
2. Put your key in `.env.openrouter`:
   - `OPENROUTER_API_KEY=...`
3. Use the OpenRouter config:
   - `configs/normalize_hashtags_openrouter.yaml`
4. Run hashtag normalization:

```bash
pipeline stage run normalize-hashtags \
  --input artifacts/enrich/hashtags.v1.json \
  --output artifacts/hashtag_normalization/mappings.v1.json \
  --config configs/normalize_hashtags_openrouter.yaml
```

Notes:
- `.env.openrouter` is ignored by git (`.env*`), so your key is not committed.
- The model is set to `openai/gpt-oss-120b:free` by default in the config.

## Resume Example

```bash
pipeline stage run-many \
  --stages clean,enrich,analyze \
  --event superbowl \
  --year 2024 \
  --output-root artifacts \
  --config configs/pipeline.yaml \
  --skip-completed
```

## Deferred (Non-MVP)

- Human review UI/work queues
- Remote artifact store/registry
- Multi-agent adjudication
- Scheduler integrations
