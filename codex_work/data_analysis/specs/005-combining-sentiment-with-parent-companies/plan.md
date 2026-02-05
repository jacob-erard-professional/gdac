# Implementation Plan: Combining Sentiment with Parent Companies

**Branch**: `005-combining-sentiment-with-parent-companies` | **Date**: 2026-02-05 | **Spec**: `specs/005-combining-sentiment-with-parent-companies/spec.md`
**Input**: Feature specification from `/specs/005-combining-sentiment-with-parent-companies/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See
`.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement a deterministic analytics step that joins BERTweet sentiment outputs
with parent-company groupings and enriched tweet metadata to produce per-parent
company sentiment impact summaries. This includes a standalone CLI command,
optional pipeline integration, and year-scoped outputs under analytics.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: pandas, typer, pydantic, pyarrow
**Storage**: year-scoped files under `data/*/<year>/`, `outputs/analytics/<year>/`, `sentiment/*/<year>/`
**Testing**: pytest
**Target Platform**: Linux CLI environment
**Project Type**: data pipeline / analytics CLI
**Performance Goals**: deterministic joins over yearly datasets without OOM
**Constraints**: deterministic outputs, raw-data immutability, explicit paths
**Scale/Scope**: per-year runs, one record per tweet, parent-level summaries

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Data is year-scoped using `data/raw/<year>/`, `data/processed/<year>/`,
  `data/enriched/<year>/`, `outputs/analytics/<year>/`.
- Raw input files are read-only after ingest; plan includes safeguards against writes
  to `data/raw`.
- Pipeline stages are independently runnable (`ingest`, `clean`, `process`,
  `analyze`, optional `visualize`, `export`) with explicit inputs/outputs.
- CLI design supports `--year` or `--data-dir`, single-stage runs, per-year full runs,
  and all-years full runs.
- Processing approach is deterministic and memory-safe for large datasets
  (chunked/streaming where applicable).
- Analytics scope includes required coverage (volume, sentiment over time, time buckets,
  ROI proxies, relationship analysis, event alignment, text/network analysis).
- Documentation impact is identified; README updates are planned for any new capability.

## Project Structure

### Documentation (this feature)

```text
specs/005-combining-sentiment-with-parent-companies/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── pipeline/
│   ├── stages/
│   └── orchestrator.py
├── sentiment/
├── cli/
└── analytics/

data/
├── raw/
│   └── <year>/
├── processed/
│   └── <year>/
├── enriched/
│   └── <year>/
└── analytics/
    └── <year>/

outputs/
└── analytics/
    └── <year>/

tests/
├── integration/
└── unit/
```

**Structure Decision**: Add a new analytics-style joiner under `src/sentiment/` or
`src/analytics/` with a pipeline stage adapter in `src/pipeline/stages/`, a CLI
entrypoint in `src/cli/`, and year-scoped outputs under `outputs/analytics/<year>/`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
