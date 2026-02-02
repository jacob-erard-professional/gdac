# Tasks: Super Bowl X Analytics Pipeline

**Input**: Design documents from `/home/jacoberard/agent_practice/gdac/specs/001-build-superbowl-analytics-pipeline/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Include test tasks for every user story. Testability and repeatability are required by the constitution.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths in this file use the Python pipeline structure defined in `plan.md`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and baseline project structure

- [X] T001 Create project directories in `src/`, `tests/`, `data/`, and `outputs/` per `specs/001-build-superbowl-analytics-pipeline/plan.md`
- [X] T002 Create Python package markers in `src/orchestrator/__init__.py`, `src/ingestion/__init__.py`, `src/cleaning/__init__.py`, `src/enrichment/__init__.py`, `src/analysis/__init__.py`, `src/visualization/__init__.py`, and `src/reporting/__init__.py`
- [X] T003 [P] Create MVP dependency manifest in `pyproject.toml` for Phases 1-3 only, and add commented placeholders for deferred US2/US3 dependencies
- [X] T004 [P] Configure linting/type/test tooling in `pyproject.toml` and `pytest.ini`
- [X] T005 [P] Create base configuration files `config/pipeline.yaml`, `config/event_windows.yaml`, `config/keywords.yaml`, and `config/kpi_definitions.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Implement shared run context and metadata models in `src/common/schemas/run_context.py`
- [X] T007 [P] Implement US1-only shared entity schemas in `src/common/schemas/entities.py` (PipelineRun, RawSocialRecord, CleanedSocialRecord, minimal EnrichedSocialRecord, YearlyKPIResult, manifest/artifact index), deferring US2/US3 schemas
- [X] T008 [P] Implement stage result and validation report schemas in `src/common/schemas/stage_result.py`
- [X] T009 Implement structured JSON logging utilities in `src/common/logging/structured_logger.py`
- [X] T010 [P] Implement filesystem IO utilities for partitioned paths in `src/common/io/storage.py`
- [X] T011 Implement stage interface contract in `src/common/stage_interface.py`
- [X] T012 Implement orchestrator skeleton with stage chaining in `src/orchestrator/run_pipeline.py`
- [X] T013 [P] Implement CLI argument parsing (`--event`, `--year`, `--config`) in `src/orchestrator/cli.py`
- [X] T014 Implement run manifest writer in `src/orchestrator/manifest.py`
- [X] T015 [P] Add MVP-scoped foundational unit tests for schemas, logging utilities, and storage utilities in `tests/unit/test_foundation.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Produce Year-Specific Analytics Outputs (Priority: P1) 🎯 MVP

**Goal**: Run one year end-to-end and produce cleaned data, KPIs, visuals, and summary outputs

**Independent Test**: Execute a single run for one year and verify all expected output artifacts exist with quality summaries.

### Tests for User Story 1 (REQUIRED) ⚠️

- [X] T016 [P] [US1] Create stage validation unit tests in `tests/unit/test_stage_validations_us1.py`
- [X] T017 [P] [US1] Create orchestrator integration test for single-year run in `tests/integration/test_single_year_pipeline_us1.py`
- [X] T018 [P] [US1] Create CLI-run contract test in `tests/contract/test_cli_run_manifest_contract.py` to validate run manifest and artifact index schema conformance (service-style API contract testing deferred beyond MVP)

### Implementation for User Story 1

- [X] T019 [P] [US1] Implement ingestion module in `src/ingestion/ingest_x_data.py`
- [X] T020 [P] [US1] Implement cleaning module with rejection reasons in `src/cleaning/clean_records.py`
- [X] T021 [P] [US1] Implement minimal/no-op enrichment module in `src/enrichment/enrich_records.py` that preserves stage boundaries and provides only fields required for US1 KPI computation
- [X] T022 [US1] Implement KPI computation pipeline in `src/analysis/compute_kpis.py`
- [X] T023 [US1] Implement visualization artifact generation in `src/visualization/generate_visuals.py`
- [X] T024 [US1] Implement reporting module for yearly summary output in `src/reporting/generate_summary.py`
- [X] T025 [US1] Wire US1 modules into orchestrator execution flow in `src/orchestrator/run_pipeline.py`
- [X] T026 [US1] Implement stage-level quality summary logging in `src/orchestrator/quality_reporting.py`
- [X] T027 [US1] Implement year-partitioned artifact writing in `src/orchestrator/artifact_writer.py`

**Checkpoint**: User Story 1 is fully functional and independently testable

---

## Phase 4: User Story 2 - Compare Multiple Years Consistently (Priority: P2)

**Goal**: Enable consistent cross-year execution and comparison-ready outputs

**Independent Test**: Run at least two years and confirm schema/metric consistency plus deterministic rerun outputs.

### Tests for User Story 2 (REQUIRED) ⚠️

- [X] T028 [P] [US2] Create integration test for multi-year execution in `tests/integration/test_multi_year_pipeline_us2.py`
- [X] T029 [P] [US2] Create regression rerun determinism test in `tests/regression/test_rerun_determinism_us2.py`
- [X] T030 [P] [US2] Create contract test for `GET /runs/{run_id}/artifacts` in `tests/contract/test_artifacts_contract.py`

### Implementation for User Story 2

- [X] T031 [P] [US2] Implement KPI definition loader/version resolver in `src/analysis/kpi_definition_loader.py`
- [X] T032 [US2] Implement cross-year comparison assembler in `src/analysis/build_year_over_year_views.py`
- [X] T033 [US2] Enforce stable output schema/version checks in `src/orchestrator/schema_guard.py`
- [X] T034 [US2] Implement deterministic sort/seed controls in `src/orchestrator/determinism.py`
- [X] T035 [US2] Extend manifest with config hash and KPI definition version in `src/orchestrator/manifest.py`
- [X] T036 [US2] Implement multi-year run helper CLI path in `src/orchestrator/cli.py`

**Checkpoint**: User Stories 1 and 2 work independently and support cross-year comparison

---

## Phase 5: User Story 3 - Deliver Stakeholder-Ready Insights (Priority: P3)

**Goal**: Produce white paper and executive-ready narrative and visual deliverables

**Independent Test**: Validate that generated narratives cite KPI outputs, include assumptions/limitations, and support stakeholder presentation use.

### Tests for User Story 3 (REQUIRED) ⚠️

- [X] T037 [P] [US3] Create integration test for report bundle generation in `tests/integration/test_reporting_bundle_us3.py`
- [X] T038 [P] [US3] Create contract test for `GET /kpi-definitions` in `tests/contract/test_kpi_definitions_contract.py`
- [X] T039 [P] [US3] Create narrative traceability test in `tests/regression/test_summary_traceability_us3.py`

### Implementation for User Story 3

- [X] T040 [P] [US3] Create white paper summary template in `src/reporting/templates/white_paper.md.j2`
- [X] T041 [P] [US3] Create executive summary template in `src/reporting/templates/executive_brief.md.j2`
- [X] T042 [US3] Implement narrative generation with methodology/limitations sections in `src/reporting/generate_narratives.py`
- [X] T043 [US3] Implement KPI-to-claim traceability mapping in `src/reporting/traceability.py`
- [X] T044 [US3] Add infographic export packaging in `src/visualization/export_infographic_assets.py`
- [X] T045 [US3] Integrate stakeholder report bundle output in `src/orchestrator/artifact_writer.py`

**Checkpoint**: All user stories are independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T046 [P] Update run instructions and validation workflow in `specs/001-build-superbowl-analytics-pipeline/quickstart.md`
- [X] T047 Performance-tune heavy transformations and KPI aggregation in `src/analysis/compute_kpis.py`
- [X] T048 [P] Add cross-year consistency fixtures in `tests/regression/fixtures/cross_year/`
- [X] T049 [P] Add end-to-end smoke script in `scripts/run_smoke_pipeline.sh`
- [X] T050 Run full test suite and capture evidence in `specs/001-build-superbowl-analytics-pipeline/checklists/requirements.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - can start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 - BLOCKS all user stories
- **Phase 3 (US1)**: Depends on Phase 2; establishes MVP
- **Phase 4 (US2)**: Depends on Phase 3 data contracts and KPI baseline
- **Phase 5 (US3)**: Depends on Phase 3 outputs and Phase 4 KPI consistency metadata
- **Phase 6 (Polish)**: Depends on all target stories being complete

### User Story Dependencies

- **US1 (P1)**: Independent after foundation; no dependency on US2/US3
- **US2 (P2)**: Uses US1 baseline KPI/output structure and introduces deferred service-style API contract testing and cross-year schema expansion
- **US3 (P3)**: Uses US1 outputs and US2 comparability metadata, and introduces deferred stakeholder-traceability schema expansion

### Dependency Graph

- US1 -> US2 -> US3

### Within Each User Story

- Tests first (fail before implementation)
- Data/model logic before orchestration wiring
- Generation logic before artifact packaging
- Story-specific validation before moving to next story

---

## Parallel Opportunities

- **Setup**: T003, T004, T005 can run in parallel after T001-T002
- **Foundational**: T007, T008, T010 can run in parallel after T006
- **US1**: T016-T018 and T019-T021 are parallelizable; T022+ converge sequence
- **US2**: T028-T030 and T031 can run in parallel before integration tasks
- **US3**: T037-T039 and T040-T041 can run in parallel before T042-T045
- **Polish**: T046, T048, T049 can run in parallel before T050

## Parallel Example: User Story 1

```bash
Task: "T016 [US1] stage validation unit tests in tests/unit/test_stage_validations_us1.py"
Task: "T017 [US1] single-year integration test in tests/integration/test_single_year_pipeline_us1.py"
Task: "T018 [US1] CLI manifest/artifact index contract test in tests/contract/test_cli_run_manifest_contract.py"
Task: "T019 [US1] ingestion module in src/ingestion/ingest_x_data.py"
Task: "T020 [US1] cleaning module in src/cleaning/clean_records.py"
Task: "T021 [US1] minimal/no-op enrichment module in src/enrichment/enrich_records.py"
```

## Parallel Example: User Story 2

```bash
Task: "T028 [US2] multi-year integration test in tests/integration/test_multi_year_pipeline_us2.py"
Task: "T029 [US2] rerun determinism regression test in tests/regression/test_rerun_determinism_us2.py"
Task: "T030 [US2] artifacts contract test in tests/contract/test_artifacts_contract.py"
Task: "T031 [US2] KPI definition loader in src/analysis/kpi_definition_loader.py"
```

## Parallel Example: User Story 3

```bash
Task: "T037 [US3] reporting bundle integration test in tests/integration/test_reporting_bundle_us3.py"
Task: "T038 [US3] KPI definitions contract test in tests/contract/test_kpi_definitions_contract.py"
Task: "T039 [US3] summary traceability regression test in tests/regression/test_summary_traceability_us3.py"
Task: "T040 [US3] white paper template in src/reporting/templates/white_paper.md.j2"
Task: "T041 [US3] executive summary template in src/reporting/templates/executive_brief.md.j2"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Validate single-year run output integrity and quality summaries
5. Demo MVP with one Super Bowl year

### Incremental Delivery

1. Deliver US1 for yearly pipeline baseline
2. Add US2 for year-over-year comparison and deterministic reruns
3. Add US3 for stakeholder-ready narrative and infographic bundles
4. Polish performance and regression stability

### Parallel Team Strategy

1. Team completes Setup + Foundational together
2. Developer A: US1 core modules
3. Developer B: US2 comparability and determinism
4. Developer C: US3 reporting and packaging
5. Integrate and validate in Phase 6

---

## Notes

- All tasks follow required checklist format: checkbox, ID, optional `[P]`, required `[US#]` in story phases, and exact file path
- Each user story has independent test criteria and dedicated test tasks
- Contract tests map to `contracts/pipeline-orchestrator.openapi.yaml`
- Data-model entities are mapped to stage/module tasks in US1-US3
- MVP deferrals are explicit: service-style API contract testing and US2/US3-only schema depth are deferred beyond Phase 3
