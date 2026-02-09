# Feature Specification: Agentic Emotion Classification for Brand Analysis

**Feature Branch**: `007-agentic-emotion-classification`
**Date**: 2026-02-07
**Input**: User request to add a deterministic, agentic workflow for emotion classification (committee + supervisor) with representative examples per brand.

## Summary

Implement an agentic, offline, batch workflow to classify emotions in brand-related tweets.
The workflow should reduce false positives (especially false joy), identify neutral/no-emotion
tweets, and produce example-backed outputs suitable for analysis and presentation.

## User Stories

### User Story 1 - Run agentic emotion classification for a year (P1)
As an analyst, I want to run agentic emotion classification over brand-related tweets so I can
see which emotions are present with representative examples per brand.

**Acceptance Criteria**
1. Given enriched tweets and brand-group artifacts, running the command produces year-scoped
   outputs under `outputs/analytics/<year>/` (and aux artifacts under `outputs/aux/<year>/`).
2. Neutral/no-emotion tweets are explicitly labeled and excluded from emotion examples.
3. The workflow is deterministic for identical inputs.

### User Story 2 - Optional pipeline integration (P2)
As a maintainer, I want to run agentic emotion classification as an optional pipeline step so
I can include it in automated runs without changing defaults.

**Acceptance Criteria**
1. A `--with-agentic-emotion` flag runs the new step; default runs are unchanged.
2. The step runs after brand grouping artifacts exist.

## Functional Requirements

- **FR-001**: Implement a committee of agents:
  - Emotion presence detector (is any strong emotion present?).
  - Sarcasm/irony detector.
  - Dominant emotion classifier (only when justified).
  - Supervisor arbiter combining the above into a final label.
- **FR-002**: Output strict JSON for each agent with per-tweet decisions and confidence.
- **FR-003**: Supervisor emits final label from a fixed taxonomy plus `neutral/no-emotion`.
- **FR-004**: Produce example-backed outputs: per-brand, per-emotion examples (highest-confidence).
- **FR-005**: Provide CLI entrypoint for year or data-dir, with batch size and dry-run.
- **FR-006**: Optional pipeline hook (flag only; default pipeline unchanged).
- **FR-007**: Deterministic ordering and reproducible outputs.

## Non-Goals

- Model training or fine-tuning
- Real-time inference or API service
- Web browsing or search tools
- Changing upstream ingestion or cleaning behavior

## Inputs

- `data/enriched/<year>/enriched.csv` (tweet text, metadata, brand/ad tags)
- `outputs/analytics/<year>/brand_groups.json`
- `outputs/analytics/<year>/parent_company_groups.json` (optional for downstream joins)

## Outputs

- `outputs/analytics/<year>/agentic_emotion_summary.json` (per-brand counts and rates)
- `outputs/analytics/<year>/agentic_emotion_examples.json` (per-brand, per-emotion tweet examples)
- `outputs/aux/<year>/agentic_emotion_partial.jsonl` (batch progress / recoverability)
- `outputs/aux/<year>/agentic_emotion_parse_failures.txt` (raw outputs on parse failure)

## Validation & Testing

- Unit tests for deterministic outputs and label taxonomy enforcement.
- Integration test for CLI and pipeline flag behavior.
- Tests for neutral/no-emotion classification on weakly expressive text.

