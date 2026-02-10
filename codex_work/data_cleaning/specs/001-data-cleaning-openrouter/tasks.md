---

description: "Task list for deterministic Twitter (X) data cleaning with OpenRouter agents"
---

# Tasks: Deterministic Twitter (X) Data Cleaning + OpenRouter Agents

**Input**: Design documents from `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/specs/001-data-cleaning-openrouter/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Initialize repository structure, README scaffold, and config directory in `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/README.md` and `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/config/`
- [X] T002 [P] Define column registry with Twitter column enumeration and classification in `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/ingest/column_registry.py` and `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/config/column_registry.yaml`
- [X] T003 [P] Define agent I/O schemas with failure and abstention rules in `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/brand/agent_schemas.py` and `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/brand/agent_schemas.json`
- [X] T004 [P] Define OpenRouter configuration contract in `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/config/openrouter.schema.json`
- [X] T005 [P] Define manifest schema including agent metadata fields in `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/ingest/manifest_schema.json`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [X] T006 Implement CSV ingestion with multi-file support from `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/data/raw/<year>/` in `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/ingest/csv_loader.py`
- [X] T007 [P] Implement structural validation for required columns (`id`, `text`, `brand`) in `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/ingest/structural_validation.py`
- [X] T008 [P] Implement quarantine handling for malformed rows in `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/ingest/quarantine.py`
- [X] T009 [P] Emit ingestion manifest in `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/ingest/manifest.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Deterministic Cleaning Pipeline (Priority: P1)

**Goal**: Deterministic normalization for text and brand while preserving raw columns

**Independent Test**: Run deterministic steps twice on the same input and compare hashes/manifests

### Implementation for User Story 1

- [X] T010 [P] [US1] Preserve original text by copying `text` to `text_original` in `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/text/preserve_original.py`
- [X] T011 [P] [US1] Implement text normalization (Unicode, whitespace, configurable casing) in `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/text/normalize_text.py`
- [X] T012 [P] [US1] Implement deterministic URL handling in `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/text/url_handling.py`
- [X] T013 [P] [US1] Add retweet and duplicate flags (no deletion) in `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/text/noise_flags.py`
- [X] T014 [US1] Emit text-cleaning manifest in `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/text/manifest.py`
- [X] T015 [P] [US1] Preserve original brand by copying `brand` to `brand_original` in `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/brand/preserve_original.py`
- [X] T016 [P] [US1] Implement canonical brand normalization with alias mapping in `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/brand/normalize_brand.py`
- [X] T017 [P] [US1] Add brand validity flags (empty, unknown, alias-resolved) in `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/brand/brand_flags.py`
- [X] T018 [US1] Emit brand-normalization manifest in `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/brand/manifest.py`

**Checkpoint**: User Story 1 is fully functional and deterministic

---

## Phase 4: User Story 2 - OpenRouter Agent Classification (Priority: P2)

**Goal**: Stateless agent-based brand relevance classification with auditable outputs

**Independent Test**: Run classification with cached outputs and verify replayed results

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement brand relevance agent contract and prompt versioning in `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/brand/relevance_agent.py`
- [X] T020 [P] [US2] Implement OpenRouter inference client with retries and backoff in `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/brand/openrouter_client.py`
- [X] T021 [P] [US2] Implement agent execution controls (batching, rate limits, cost ceilings) in `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/brand/agent_executor.py`
- [X] T022 [P] [US2] Implement agent output validation and quarantine in `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/brand/output_validation.py`
- [X] T023 [US2] Emit relevance-classification manifest with model and prompt metadata in `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/brand/relevance_manifest.py`
- [X] T024 [US2] Assemble clean dataset by merging deterministic and agent outputs in `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/cleaning/assemble_clean.py`

**Checkpoint**: User Story 2 is fully functional with auditable agent outputs

---

## Phase 5: User Story 3 - CLI + Config Driven Operation (Priority: P3)

**Goal**: Run single steps or full pipeline via CLI with config-driven controls

**Independent Test**: Run a single step via CLI with custom directories and validate outputs

### Implementation for User Story 3

- [X] T025 [US3] Implement CLI entry points for running steps and full pipeline in `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/scripts/pipeline.py`

**Checkpoint**: User Story 3 is fully functional and independently testable

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T029 Add unit tests for text normalization and URL handling in `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/tests/unit/test_text_normalization.py` and `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/tests/unit/test_url_handling.py`
- [X] T030 Add unit tests for agent output validation and JSON parsing in `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/tests/unit/test_agent_output_validation.py` and `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/tests/unit/test_relevance_agent.py`
- [X] T026 Add structured logging, agent call counts, and cost summaries in `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/orchestrator/logging.py`
- [X] T027 Update documentation for agent workflow, OpenRouter configuration, model swapping, and derived columns in `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/README.md`
- [X] T028 Implement safe parallel execution helpers using `concurrent.futures` and file locks (partitioned outputs + lockfiles) in `/home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/orchestrator/parallelism.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2)
- **User Story 2 (P2)**: Depends on User Story 1 outputs
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) and parallel to US2

### Within Each User Story

- Schema and contracts before implementation
- Deterministic steps before agent invocation
- Validation before manifest emission

### Parallel Opportunities

- T002, T003, T004, T005 can run in parallel after T001
- T010, T011, T012, T013 can run in parallel after T006-T009
- T015, T016, T017 can run in parallel after T006-T009
- T019, T020, T021, T022 can run in parallel after T015-T018

---

## Parallel Example: User Story 1

```bash
Task: "Preserve original text in /home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/text/preserve_original.py"
Task: "Implement text normalization in /home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/text/normalize_text.py"
Task: "Implement URL handling in /home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/text/url_handling.py"
```

---

## Parallel Example: User Story 2

```bash
Task: "Implement OpenRouter client in /home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/brand/openrouter_client.py"
Task: "Implement agent executor in /home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/brand/agent_executor.py"
Task: "Implement output validation in /home/jacoberard/agent_practice/gdac/codex_work/data_cleaning/src/brand/output_validation.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deliver deterministic pipeline
3. Add User Story 2 → Test independently → Deliver agentic classification
4. Add User Story 3 → Test independently → Deliver CLI orchestration
5. Polish documentation and observability
