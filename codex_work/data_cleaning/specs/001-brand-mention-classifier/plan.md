# Implementation Plan: Brand Mention Classifier Prompt

**Branch**: `[001-brand-mention-classifier]` | **Date**: 2026-02-10 | **Spec**: `specs/001-brand-mention-classifier/spec.md`
**Input**: Feature specification from `/specs/001-brand-mention-classifier/spec.md`

**Note**: This template is filled in by the planning workflow. Align it with
the repository constitution in `.specify/memory/constitution.md`.

## Summary

Create a simple, Python-first CLI that reads tweet CSVs with a `brand` column
and produces `is_about_brand` classifications using an LLM prompt via
OpenRouter. The prompt prioritizes `text` while allowing other columns as
secondary disambiguation signals. Output includes optional `confidence` and
`rationale` for auditability. The CLI accepts a `--model` option and reads the
OpenRouter API key from an exported environment variable.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: Standard library (`csv`, `json`, `argparse`) plus a
minimal HTTP client for OpenRouter (e.g., `httpx` or `requests`)  
**Storage**: N/A (file-based input/output)  
**Testing**: `pytest`  
**Target Platform**: Local CLI on macOS/Linux  
**Project Type**: Single project  
**Performance Goals**: Process 10k rows in under 2 minutes on a standard laptop  
**Constraints**: All artifacts remain under repo; README updated for every change;
OpenRouter API key supplied via environment variable when running the CLI; CSV
columns may be missing/empty and must be handled robustly  
**Scale/Scope**: Single CLI workflow, 10k-row batch processing

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Simplicity: No unnecessary abstractions; complexity justified in this plan.
- Testability: Every user story has test coverage defined and feasible.
- Documentation: README and usage docs update plan included.
- Python-first: Default to Python; any exception has measured performance evidence.
- Performance evidence: Targets and benchmarks defined for critical paths.
- Repository-local artifacts: All outputs remain under repo (except `/tmp`).

**Gate Status**: PASS

## Project Structure

### Documentation (this feature)

```text
specs/001-brand-mention-classifier/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── cli/
│   └── classify_brand_mentions.py
├── lib/
│   ├── prompt_builder.py
│   └── csv_io.py
└── models/
    └── schemas.py

tests/
├── integration/
│   └── test_cli_batch.py
└── unit/
    ├── test_prompt_builder.py
    └── test_csv_io.py
```

**Structure Decision**: Single-project CLI layout for simplicity and testability.

## Post-Design Constitution Check

- Simplicity: Single CLI workflow with minimal dependencies.
- Testability: Deterministic prompt output and unit/integration tests planned.
- Documentation: README update required in implementation tasks.
- Python-first: Python 3.11 only; no non-Python components planned.
- Performance evidence: Batch target defined in spec and plan.
- Repository-local artifacts: All outputs stay under repo; temp in `/tmp` only.

**Gate Status**: PASS

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |
