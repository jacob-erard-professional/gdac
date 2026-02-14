# Implementation Plan: Brand List Classifier

**Branch**: `[002-brand-list-classifier]` | **Date**: 2026-02-13 | **Spec**: `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/specs/002-brand-list-classifier/spec.md`
**Input**: Feature specification from `/specs/002-brand-list-classifier/spec.md`

**Note**: This template is filled in by the planning workflow. Align it with
the repository constitution in `.specify/memory/constitution.md`.

## Summary

Implement a brand-list classification workflow that reuses existing
brand-relevance components. The workflow ingests a tweet CSV, keeps all rows in
output, skips OpenRouter calls for rows where `is_about_brand` is true, and
classifies only candidate rows against brands loaded from a one-column CSV with
header `brand`. Candidate rows must output exactly one category:
`listed_brand`, `new_brand`, or `no_brand`; skipped rows output
`category=skipped` with deterministic default fields.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: Python standard library (`csv`, `json`, `argparse`,
`urllib`) plus existing in-repo modules under `src/lib/`  
**Storage**: N/A (file-based CSV input/output)  
**Testing**: `pytest`  
**Target Platform**: Local CLI (Linux/macOS)  
**Project Type**: Single project  
**Performance Goals**: Maintain throughput within 20% of current
brand-relevance workflow for equivalent candidate-row volume  
**Constraints**: Reuse existing data_cleaning modules where behavior is
compatible; OpenRouter env-key auth remains unchanged; all artifacts remain in
repo; README updates required  
**Scale/Scope**: 10k-row CSV batches, pre-filtering by `is_about_brand`,
brand-list classification for candidate rows only

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Simplicity: Reuse existing parser/client/output modules and add minimal
  feature-specific logic.
- Testability: Unit and integration tests cover skip behavior, brand category
  output, and deterministic skipped-row fields.
- Documentation: README and quickstart document CSV inputs and CLI usage.
- Python-first: Python-only implementation.
- Performance evidence: Candidate-row-only calls preserve expected throughput.
- Repository-local artifacts: All generated docs/spec artifacts stay under repo.

**Gate Status**: PASS

## Project Structure

### Documentation (this feature)

```text
specs/002-brand-list-classifier/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── openapi.yaml
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── cli/
│   ├── classify_brand_mentions.py        # existing workflow
│   └── classify_brand_list.py            # new workflow entrypoint
├── lib/
│   ├── classifier.py                     # existing OpenRouter batch execution
│   ├── csv_io.py                         # existing CSV parsing/writing
│   ├── openrouter_client.py              # existing OpenRouter client
│   ├── prompt_builder.py                 # extend prompt generation
│   └── brand_list_classifier.py          # new brand-list logic
└── models/
    └── schemas.py                        # extend result schema

tests/
├── integration/
│   └── test_cli_brand_list.py
└── unit/
    ├── test_brand_list_classifier.py
    └── test_brand_list_prompt_builder.py
```

**Structure Decision**: Single-project reuse-first design; add new entrypoint
and minimal brand-list specific logic.

## Post-Design Constitution Check

- Simplicity: Architecture extends existing workflow with minimal branching.
- Testability: Category enforcement and skip-row defaults are deterministic.
- Documentation: Inputs/outputs and run commands documented for operators.
- Python-first: No non-Python dependencies introduced.
- Performance evidence: Skipping true rows minimizes model calls and cost.
- Repository-local artifacts: Files and outputs remain under `data_cleaning`.

**Gate Status**: PASS

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |
