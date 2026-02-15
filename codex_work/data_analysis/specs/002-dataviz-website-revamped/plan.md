# Implementation Plan: Dataset Comparison Visualization Website

**Branch**: `002-dataviz-website-revamped` | **Date**: 2026-02-14 | **Spec**: [/home/jacoberard/agent_practice/gdac/codex_work/data_analysis/specs/002-dataviz-website-revamped/spec.md](/home/jacoberard/agent_practice/gdac/codex_work/data_analysis/specs/002-dataviz-website-revamped/spec.md)
**Input**: Feature specification from `/specs/002-dataviz-website-revamped/spec.md`

## Summary

Implement a year-driven website view that compares regular and full datasets side by side for years where both datasets exist, using required word clouds and dual tweet-style cards with deterministic, deduplicated navigation.

## Technical Context

**Language/Version**: JavaScript (ES2022) + React
**Primary Dependencies**: Existing `site/` stack, chart rendering library in current website, browser-side JSON/CSV parsing utilities
**Storage**: Read-only repository files from `outputs/analytics/<year>` and `outputs/analytics/<year>_full`, plus raw CSV sources for brand/text extraction
**Testing**: pytest for data transformation helpers + frontend behavior verification with deterministic fixture datasets
**Target Platform**: Local and hosted browser environment for `site/`
**Project Type**: Single-repo frontend enhancement consuming pipeline artifacts
**Performance Goals**: Initial render for selected year in <=10 seconds; year switch refresh in <=2 seconds for typical artifact sizes
**Constraints**: Deterministic transformations, zero writes to `data/raw` and analytics inputs, year-scoped loading only when both regular/full exist, unique tweet text per card
**Scale/Scope**: All comparable years (both dataset scopes present), five required word clouds, two tweet cards (regular/full), arrow-based browsing through full entry lists

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Data is year-scoped using `data/raw/<year>/`, `data/processed/<year>/`, `data/enriched/<year>/`, `outputs/analytics/<year>/`.
  - **PASS**: Feature consumes explicit year folders and full counterparts (`<year>_full`) without cross-year mixing.
- Raw input files are read-only after ingest; plan includes safeguards against writes to `data/raw`.
  - **PASS**: Design is read-only and transformation-only in memory.
- Pipeline stages are independently runnable (`ingest`, `clean`, `process`, `analyze`, optional `visualize`, `export`) with explicit inputs/outputs.
  - **PASS**: No stage contract modifications are required.
- CLI design supports `--year` or `--data-dir`, single-stage runs, per-year full runs, and all-years full runs.
  - **PASS**: This feature does not alter CLI execution contracts.
- Processing approach is deterministic and memory-safe for large datasets (chunked/streaming where applicable).
  - **PASS**: Deterministic normalization and bounded per-year data loading strategy are planned.
- Analytics scope includes required coverage (volume, sentiment over time, time buckets, ROI proxies, relationship analysis, event alignment, text/network analysis).
  - **PASS**: Feature is a visualization consumer of existing analytics outputs.
- Documentation impact is identified; README updates are planned for any new capability.
  - **PASS**: Quickstart and README update are included in scope.

## Project Structure

### Documentation (this feature)

```text
/home/jacoberard/agent_practice/gdac/codex_work/data_analysis/specs/002-dataviz-website-revamped/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── comparison-api.yaml
└── tasks.md
```

### Source Code (repository root)

```text
/home/jacoberard/agent_practice/gdac/codex_work/data_analysis/
├── site/
│   ├── src/
│   ├── package.json
│   └── README.md
├── outputs/
│   └── analytics/
├── data/
│   └── raw/
├── src/
└── tests/
```

**Structure Decision**: Reuse existing `site/` application. Add data loading/transformation modules and comparison UI components under `site/src` only.

## Phase 0: Outline & Research

1. Research deterministic year list generation requiring both regular and full dataset presence.
2. Research normalization strategy for required word clouds across JSON metrics and CSV inputs.
3. Research deterministic duplicate-text elimination rules for tweet cards.
4. Research handling for missing `is_about_brand` while honoring clarified behavior (`treat as false`).
5. Research non-blocking UX for missing file/column states.

## Phase 1: Design & Contracts

1. Define year option, dataset scope, word cloud term, tweet card, and navigator entities with validation rules.
2. Define API contracts for year discovery, year comparison payload, and tweet card data retrieval.
3. Define quickstart with exact required files and validation checks.
4. Run agent context update script for Codex.

## Post-Design Constitution Check

- **PASS**: Year-scoped data organization and read-only source handling preserved.
- **PASS**: Modular pipeline/CLI obligations unchanged.
- **PASS**: Deterministic behavior explicit in normalization, dedupe, and navigation.
- **PASS**: Documentation outputs complete (plan/research/data-model/contracts/quickstart).

## Complexity Tracking

No constitutional violations require exemptions.
