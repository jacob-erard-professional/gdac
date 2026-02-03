# Quickstart - Modular, Resumable NLP Analytics Pipeline

## MVP Scope
- Independently runnable stages: `ingest`, `clean`, `enrich`, `analyze`, `normalize-hashtags`.
- Artifact manifest with lineage fields and schema versions.
- Subset execution with `--skip-completed` based on manifest + artifact checks.
- One agent loop for hashtag equivalence discovery with confidence scoring and audit artifacts.

## Future Extension Points
- Human review workflow UI and queues (`pending_review` triage).
- Multi-agent adjudication strategies.
- Remote artifact registry/object storage.
- Scheduler and event-driven execution adapters.

## Repository Layout

```text
.
├── src/
│   ├── pipeline/
│   │   ├── stages/
│   │   │   ├── ingest.py
│   │   │   ├── clean.py
│   │   │   ├── enrich.py
│   │   │   ├── analyze.py
│   │   │   └── normalize_hashtags.py
│   │   ├── dependencies.py
│   │   ├── orchestrator.py
│   │   └── registry.py
│   ├── artifacts/
│   │   ├── schemas/
│   │   ├── manifest_store.py
│   │   └── validator.py
│   ├── agents/
│   │   ├── interfaces.py
│   │   ├── hashtag_normalizer.py
│   │   └── providers/
│   └── cli/
│       └── main.py
├── artifacts/
│   ├── manifest.json
│   ├── ingest/
│   ├── clean/
│   ├── enrich/
│   ├── analyze/
│   └── hashtag_normalization/
└── tests/
    ├── unit/
    ├── integration/
    └── contract/
```

## Execution Flow Diagrams (text)

### 1) Single-Stage Execution
1. User runs `pipeline stage run <stage>` with explicit `--input --output --config`.
2. CLI validates artifact schema versions and declared dependencies for that stage only.
3. Stage executes and writes outputs.
4. Manifest and stage execution record are appended.

### 2) Subset Execution with Skip-Completed
1. User runs `pipeline stage run-many --stages clean,enrich,analyze --skip-completed`.
2. CLI validates selected stage set against explicit dependency declarations.
3. For each selected stage, CLI checks manifest status + output artifact existence.
4. Completed stages are marked `skipped`; remaining selected stages run in user-provided order (or validated topological order for selected set only).

### 3) Agentic Hashtag Normalization Loop
1. `enrich` stage emits hashtag candidate artifact.
2. `normalize-hashtags` stage calls `HashtagNormalizerAgent` interface.
3. Agent provider proposes equivalence classes and confidence scores.
4. Workflow persists mappings, confidence, rationale trace, and model metadata.
5. Iteration N+1 can reuse prior mappings artifact as explicit input.

## CLI Command Examples

```bash
# Bootstrap install (editable mode)
python3 -m pip install -e .

# Run one stage
pipeline stage run ingest \
  --event superbowl \
  --year 2024 \
  --output artifacts/ingest/posts.v1.jsonl \
  --config configs/ingest.yaml \
  --dry-run

# Run one stage for real
pipeline stage run clean \
  --input artifacts/ingest/posts.v1.jsonl \
  --output artifacts/clean/posts.v1.parquet \
  --config configs/clean.yaml

# Run subset with skip-completed
pipeline stage run-many \
  --stages clean,enrich,analyze \
  --event superbowl \
  --year 2024 \
  --output-root artifacts \
  --config configs/pipeline.yaml \
  --skip-completed

# Run hashtag normalization agent loop
pipeline stage run normalize-hashtags \
  --input artifacts/enrich/hashtags.v1.json \
  --output artifacts/hashtag_normalization/mappings.v1.json \
  --config configs/normalize_hashtags.yaml

# Run hashtag normalization with OpenRouter (openai/gpt-oss-120b:free)
pipeline stage run normalize-hashtags \
  --input artifacts/enrich/hashtags.v1.json \
  --output artifacts/hashtag_normalization/mappings.v1.json \
  --config configs/normalize_hashtags_openrouter.yaml

# Optional: lexicon-based emotion classification from cleaned data
pipeline stage run emotion-lexicon \
  --input artifacts/clean/posts.v1.jsonl \
  --output artifacts/emotion_lexicon/predictions.v1.json \
  --config configs/emotion_lexicon.yaml

# Optional: ML-based emotion classification from cleaned data
pipeline stage run emotion-ml \
  --input artifacts/clean/posts.v1.jsonl \
  --output artifacts/emotion_ml/predictions.v1.json \
  --config configs/emotion_ml.yaml

# Inspect manifest lineage
pipeline artifacts manifest show --path artifacts/manifest.json
```

## Design Decisions and Tradeoffs
- Filesystem-first artifact registry favors simplicity and reproducibility over query performance.
- No implicit upstream execution improves safety and resumability, but requires users to understand dependencies.
- Interface-isolated agent layer improves testability/vendor portability, at cost of extra abstraction.
- Persisting full agent traces supports governance and debugging, but increases artifact volume.
- Future review hooks are modeled now to avoid breaking changes later, even though interactive review is not in MVP.
