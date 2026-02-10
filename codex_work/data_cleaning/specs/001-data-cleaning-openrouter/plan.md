# Implementation Plan: Deterministic Twitter (X) Data Cleaning + OpenRouter Agents

**Branch**: `001-data-cleaning-openrouter` | **Date**: 2026-02-09 | **Spec**: /home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/specs/001-data-cleaning-openrouter/spec.md
**Input**: Feature specification from `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/specs/001-data-cleaning-openrouter/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a deterministic, modular cleaning pipeline for Twitter (X) CSV data that preserves
all original columns, normalizes `text`, normalizes `brand`, and invokes stateless
OpenRouter-backed LLM agents for brand relevance classification. The pipeline emits
manifest-driven, auditable artifacts with structured logs and reproducible outputs.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: pandas, pydantic, pyyaml, httpx, tenacity, orjson
**Storage**: Filesystem (CSV input, CSV/Parquet outputs, JSON manifests)
**Testing**: pytest
**Target Platform**: Linux server
**Project Type**: single
**Performance Goals**: 100k rows/min on commodity hardware for deterministic steps
**Constraints**: Deterministic outputs; no raw data mutation; strict schemas; no silent coercion
**Scale/Scope**: 1M rows per run, single-tenant CLI workflow

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Deterministic pipeline behavior defined; any non-determinism is explicitly seeded and documented.
- Step boundaries are explicit with one input directory and one output directory per step.
- Manifest and structured logging requirements are specified for each step.
- Schema validation, brand skepticism, and raw data immutability are enforced in the design.
- CLI remains thin; business logic resides in `src/`.

Status: PASS (no violations).

## Project Structure

### Documentation (this feature)

```text
/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/specs/001-data-cleaning-openrouter/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

### Source Code (repository root)

```text
/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/
├── data/
│   ├── raw/
│   ├── intermediate/
│   └── clean/
├── src/
│   ├── ingest/
│   ├── cleaning/
│   ├── brand/
│   ├── text/
│   ├── orchestrator/
│   └── config/
└── scripts/
```

**Structure Decision**: Single project with constitution-mandated modules and data layout.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations.

## Post-Design Constitution Check

- Determinism preserved; agent boundaries are explicit and cached for reproducibility.
- Step boundaries and manifest/log requirements are reflected in contracts and data model.
- Brand skepticism preserved; original `brand` remains unmodified in all schemas.
- CLI remains thin; contracts document future HTTP surface only.

Status: PASS (no violations).
