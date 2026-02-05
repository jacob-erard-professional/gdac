# Implementation Plan: Deeper Sentiment Analysis

**Branch**: `004-deeper-sentiment-analysis` | **Date**: 2026-02-04 | **Spec**: `specs/004-deeper-sentiment-analysis/spec.md`
**Input**: Feature specification from `specs/004-deeper-sentiment-analysis/spec.md`

## Summary

Add a deterministic deep-sentiment pipeline option that performs tweet-level
emotion classification into the six required labels (`joy`, `surprise`,
`anger`, `disappointment`, `excitement`, `neutral`). The feature introduces a
new CLI command and optional full-pipeline hook while preserving existing
default pipeline behavior.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: pandas, torch, transformers, typer
**Storage**: Year-scoped filesystem artifacts under `sentiment/deep/<year>/`
**Testing**: pytest (unit + integration)
**Target Platform**: Linux CLI environment
**Project Type**: data pipeline / analytics CLI extension
**Performance Goals**: deterministic, batched inference on yearly data without OOM
**Constraints**: immutable raw data, explicit paths, deterministic outputs,
required six-label taxonomy
**Scale/Scope**: one-year or all-years execution, one output record per valid tweet

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- PASS: Feature remains year-scoped and writes only to derived output paths.
- PASS: New capability is independently runnable and optionally pipeline-invoked.
- PASS: Deterministic ordering and persisted artifacts are required.
- PASS: Raw input immutability remains enforced by existing guardrails.
- PASS: README update requirement included in tasks.

## Project Structure

### Documentation (this feature)

```text
specs/004-deeper-sentiment-analysis/
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── cli/
│   ├── main.py
│   ├── run.py
│   └── deep_sentiment.py
├── sentiment/
│   └── deep_emotion.py
├── pipeline/
│   ├── config.py
│   ├── orchestrator.py
│   └── stages/
│       └── deep_sentiment.py
└── utils/
    └── io.py

tests/
├── unit/
│   ├── test_deep_sentiment_core.py
│   └── test_cli_deep_sentiment.py
└── integration/
    └── test_with_deep_sentiment_pipeline_mode.py
```

**Structure Decision**: Implement as an additive sentiment module and CLI command,
with optional orchestration hook controlled by an explicit run flag.

## Phase 0: Model Selection Decision

Evaluate and lock one default pretrained checkpoint that can deterministically
produce the required six-label taxonomy either directly or via a strict,
documented canonical mapping. Keep explicit model override support.

## Phase 1: Interface and Contract Design

- Define deep-sentiment input contract (tweet id, text, year, hashtag extraction source).
- Define output JSON schema and metadata contract.
- Define model label canonicalization and validation behavior.

## Phase 2: Implementation & Integration

- Implement deep emotion inference core with batching and deterministic ordering.
- Add CLI command for standalone execution.
- Add optional pipeline integration flag for full runs.

## Phase 3: Validation & Documentation

- Add unit/integration tests for deterministic outputs and pipeline flag behavior.
- Update README with usage, output schema, and model limitations.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
