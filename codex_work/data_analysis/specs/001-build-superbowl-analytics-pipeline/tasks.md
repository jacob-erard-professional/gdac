# Tasks: Twitter Super Bowl Analytics Pipeline

**Input**: Design documents from `/home/jacoberard/agent_practice/gdac/codex_work/data_analysis/specs/001-build-superbowl-analytics-pipeline/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Include pytest coverage for deterministic execution, raw-data immutability,
stage isolation, contract behavior, and per-story acceptance criteria.

**Organization**: Tasks are grouped by user story so each story is independently
implementable and testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Parallelizable task (different files, no dependency on incomplete tasks)
- **[Story]**: Story label for user story phases only (`[US1]`, `[US2]`, `[US3]`)
- Every task includes an exact file path

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize repository layout and baseline tooling.

- [X] T001 Create repository directories in `data/raw/`, `data/processed/`, `data/enriched/`, `data/analytics/`, `src/cli/`, `src/pipeline/`, `src/analytics/`, `src/utils/`, `tests/unit/`, and `tests/integration/`
- [X] T002 Create package entry files in `src/__init__.py`, `src/cli/__init__.py`, `src/pipeline/__init__.py`, `src/analytics/__init__.py`, and `src/utils/__init__.py`
- [X] T003 [P] Create pinned dependency manifest in `requirements.txt` for `pandas`, `typer`, `pydantic`, `vaderSentiment`, `pyarrow`, and `pytest`
- [X] T004 [P] Create pytest configuration in `pytest.ini` for `tests/unit/` and `tests/integration/`
- [X] T005 Create canonical constants module in `src/utils/constants.py` for stage names, directory names, and metadata keys

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build contracts and orchestration required by all user stories.

**⚠️ CRITICAL**: Complete this phase before starting user story implementation.

- [X] T006 Implement configuration models in `src/pipeline/config.py` (`YearConfig`, run modes, resolved paths)
- [X] T007 Implement stage contract types in `src/pipeline/contracts.py` (`StageContract`, `RunManifest`, stage metadata)
- [X] T008 [P] Implement canonical schema validators in `src/pipeline/schema.py` using pydantic models for raw/process/enriched records
- [X] T009 [P] Implement deterministic IO helpers in `src/utils/io.py` (chunk readers, stable sorting, stable writers)
- [X] T010 Implement manifest writer and artifact tracker in `src/pipeline/manifest.py`
- [X] T011 Implement stage registry and ordering in `src/pipeline/stage_registry.py` for `ingest->clean->process->analyze->visualize->export`
- [X] T012 Implement pipeline orchestrator skeleton in `src/pipeline/orchestrator.py` with explicit input/output path checks and fail-fast upstream validation
- [X] T013 [P] Implement raw immutability guardrail in `src/utils/guards.py` to block all writes to `data/raw/`
- [X] T014 Add foundational integration test for stage ordering and required upstream artifacts in `tests/integration/test_orchestrator_prerequisites.py`
- [X] T015 Add foundational integration test for raw-data immutability in `tests/integration/test_raw_immutability.py`

**Checkpoint**: Configuration/contracts/orchestrator foundation is complete.

---

## Phase 3: User Story 1 - Run Year-Scoped Pipeline Stages from CLI (Priority: P1) 🎯 MVP

**Goal**: Execute single-stage and full-pipeline runs by year or explicit data directory.

**Independent Test**: Run `python -m src.cli run --year 2024 --stage clean` and
`python -m src.cli run --year 2024 --all`; verify only year-scoped artifacts are written.

### Tests for User Story 1

- [X] T016 [P] [US1] Add CLI argument validation tests in `tests/unit/test_cli_args.py` for `--year`, `--data-dir`, `--stage`, and `--all`
- [X] T017 [P] [US1] Add orchestrator mode tests in `tests/unit/test_orchestrator_modes.py` for stage, full-year, and all-years execution modes
- [X] T018 [US1] Add integration test for deterministic reruns in `tests/integration/test_deterministic_rerun.py`

### Implementation for User Story 1

- [X] T019 [US1] Implement CLI entrypoint and command wiring in `src/cli/main.py`
- [X] T020 [US1] Implement CLI run command parsing/dispatch in `src/cli/run.py`
- [X] T021 [US1] Implement path resolution service in `src/pipeline/path_resolution.py` for year and data-dir inputs
- [X] T022 [US1] Implement ingest stage in `src/pipeline/stages/ingest.py` with schema validation and processed outputs
- [X] T023 [US1] Implement clean stage in `src/pipeline/stages/clean.py` for deduplication, timestamp normalization, and null handling with lineage preservation
- [X] T024 [US1] Implement stage metadata emission in `src/pipeline/stage_runtime.py` (row counts, artifacts written, timestamps)
- [X] T025 [US1] Wire orchestrator-to-stage execution in `src/pipeline/orchestrator.py` for single-stage and full-year runs
- [X] T026 [US1] Document implemented CLI run modes in `README.md`

**Checkpoint**: P1 CLI + ingest/clean flow is independently runnable and testable.

---

## Phase 4: User Story 2 - Produce Required Analytics Coverage (Priority: P2)

**Goal**: Generate required per-year analytics artifacts from enriched data.

**Independent Test**: Run `python -m src.cli run --year 2024 --stage analyze`; verify
required artifacts for all analytics modules exist in `data/analytics/2024/`.

### Tests for User Story 2

- [X] T027 [P] [US2] Add unit tests for processing feature extraction in `tests/unit/test_process_features.py`
- [X] T028 [P] [US2] Add unit tests for analytics modules in `tests/unit/test_analytics_modules.py`
- [X] T029 [US2] Add integration test for analyze-stage artifact coverage in `tests/integration/test_analyze_artifacts.py`

### Implementation for User Story 2

- [X] T030 [US2] Implement process stage in `src/pipeline/stages/process.py` for text normalization, hashtags, keywords, and brand/ad tagging
- [X] T031 [P] [US2] Implement volume analytics module in `src/analytics/volume.py`
- [X] T032 [P] [US2] Implement sentiment analytics module in `src/analytics/sentiment.py`
- [X] T033 [P] [US2] Implement time-bucket analytics module in `src/analytics/time_buckets.py`
- [X] T034 [P] [US2] Implement ROI-proxy analytics module in `src/analytics/roi_proxy.py`
- [X] T035 [P] [US2] Implement relationship analytics module in `src/analytics/relationships.py`
- [X] T036 [P] [US2] Implement event-aligned analytics module in `src/analytics/event_alignment.py`
- [X] T037 [P] [US2] Implement text/network analytics module in `src/analytics/text_network.py`
- [X] T038 [US2] Implement analyze stage aggregator in `src/pipeline/stages/analyze.py` to execute all analytics modules and persist outputs
- [X] T039 [US2] Document analytics capabilities and outputs in `README.md`

**Checkpoint**: P2 analytics coverage is independently runnable and testable.

---

## Phase 5: User Story 3 - Extend Across New Years and Modules Safely (Priority: P3)

**Goal**: Support new-year runs and new-module addition without breaking existing flow.

**Independent Test**: Add `data/raw/2025/*.csv`, run same command used for 2024,
and add one new analytics module without modifying existing modules.

### Tests for User Story 3

- [X] T040 [P] [US3] Add integration test for new-year no-code-change execution in `tests/integration/test_new_year_bootstrap.py`
- [X] T041 [P] [US3] Add integration test for analytics module plug-in compatibility in `tests/integration/test_analytics_module_extension.py`
- [X] T042 [US3] Add integration test for all-years run mode in `tests/integration/test_full_all_years_mode.py`

### Implementation for User Story 3

- [X] T043 [US3] Implement all-years discovery with explicit aggregation mode in `src/pipeline/year_discovery.py`
- [X] T044 [US3] Implement optional visualize and export stage stubs in `src/pipeline/stages/visualize.py` and `src/pipeline/stages/export.py`
- [X] T045 [US3] Refactor analytics module loading to plug-in registry in `src/analytics/registry.py`
- [X] T046 [US3] Enforce module isolation and non-exclusive data ownership in `src/analytics/base.py`
- [X] T047 [US3] Add extension and multi-year usage documentation in `README.md`

**Checkpoint**: P3 extensibility requirements are independently runnable and testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final compliance, contract alignment, and release readiness.

- [X] T048 [P] Align orchestrator payloads with OpenAPI run contract in `src/pipeline/api_contract_adapter.py`
- [X] T049 [P] Add contract-response integration tests in `tests/integration/test_pipeline_contract_responses.py`
- [X] T050 Add end-to-end smoke test scenario from quickstart in `tests/integration/test_quickstart_smoke.py`
- [X] T051 Add deterministic output checksum verification utility in `src/utils/checksums.py`
- [X] T052 Validate and finalize README compliance sections in `README.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1 (Setup): starts immediately.
- Phase 2 (Foundational): depends on Setup; blocks all user stories.
- Phase 3 (US1): depends on Foundational completion.
- Phase 4 (US2): depends on Foundational completion and US1 process/analyze wiring.
- Phase 5 (US3): depends on Foundational completion and US2 analytics registry baseline.
- Phase 6 (Polish): depends on desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: no dependency on other stories after Foundational.
- **US2 (P2)**: uses processing/analyze wiring from US1; remains independently testable.
- **US3 (P3)**: validates extensibility against US1/US2 completed baseline.

### Within Each User Story

- Tests before implementation changes for that story.
- Stage/module implementation before README updates.
- Story-specific integration test must pass before moving on.

## Parallel Execution Examples

### User Story 1

```bash
# Parallel test tasks
T016 and T017

# Parallel-capable implementation (after T021)
T022 and T023
```

### User Story 2

```bash
# Parallel analytics modules
T031, T032, T033, T034, T035, T036, and T037

# Parallel test preparation
T027 and T028
```

### User Story 3

```bash
# Parallel integration tests
T040 and T041
```

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phases 1-2.
2. Complete Phase 3 (US1).
3. Validate independent test criteria for US1.
4. Demo/deploy MVP pipeline behavior.

### Incremental Delivery

1. Deliver US1 for deterministic year-scoped stage runs.
2. Add US2 analytics module coverage.
3. Add US3 extensibility and all-years workflows.
4. Complete Polish phase for contract and compliance hardening.

### Parallel Team Strategy

1. One engineer handles orchestrator/CLI core (US1).
2. One engineer implements analytics modules in parallel (US2).
3. One engineer builds extension registry and multi-year tests (US3).
