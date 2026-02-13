---

description: "Task list for implementing brand-list-classifier"
---

# Tasks: Brand List Classifier

**Input**: Design documents from `/specs/002-brand-list-classifier/`  
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Tests are REQUIRED by the constitution and included below.  
**Documentation**: README and usage updates are REQUIRED.

**Organization**: Tasks are grouped by user story so each story can be built and validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Parallelizable task (different file/no blocking dependency)
- **[Story]**: Story label (`[US1]`, `[US2]`, `[US3]`)
- Include exact file paths in task descriptions

## Path Conventions

- Single project paths: `src/`, `tests/`, `scripts/` at repository root

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare scaffolding for brand-list workflow and tests.

- [X] T001 Create CLI entrypoint scaffold in `src/cli/classify_brand_list.py`
- [X] T002 Create brand-list service scaffold in `src/lib/brand_list_classifier.py`
- [X] T003 [P] Create brand-list prompt test scaffold in `tests/unit/test_brand_list_prompt_builder.py`
- [X] T004 [P] Create brand-list logic test scaffold in `tests/unit/test_brand_list_classifier.py`
- [X] T005 [P] Create integration test scaffold in `tests/integration/test_cli_brand_list.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared prerequisites required before any user story.

**CRITICAL**: User story implementation starts only after this phase.

- [X] T006 Implement one-column brand CSV loader with `brand` header validation in `src/lib/csv_io.py`
- [X] T007 Implement `is_about_brand` true/false-like normalization helper in `src/lib/csv_io.py`
- [X] T008 Extend schema models for `listed_brand|new_brand|no_brand|skipped` in `src/models/schemas.py`
- [X] T009 Add brand-list response schema enforcement and parsing path in `src/lib/classifier.py`
- [X] T010 Add shared output merge helper for appended classification fields in `src/lib/brand_list_classifier.py`
- [X] T011 Wire CLI args (`--brand-list`, `--model`, batch/progress flags) in `src/cli/classify_brand_list.py`

**Checkpoint**: Core plumbing and validation logic complete.

---

## Phase 3: User Story 1 - Classify Candidate Tweets by Brand (Priority: P1) MVP

**Goal**: Classify candidate rows into `listed_brand`, `new_brand`, or `no_brand`.

**Independent Test**: Run candidate-only input with brand list CSV and confirm every row receives one valid non-skipped category.

### Tests for User Story 1

- [X] T012 [P] [US1] Add unit tests for category validity and required fields in `tests/unit/test_brand_list_classifier.py`
- [X] T013 [P] [US1] Add unit tests for brand-list prompt construction in `tests/unit/test_brand_list_prompt_builder.py`
- [X] T014 [P] [US1] Add integration test for listed/new/no outcomes in `tests/integration/test_cli_brand_list.py`

### Implementation for User Story 1

- [X] T015 [US1] Implement brand assignment flow for candidate rows in `src/lib/brand_list_classifier.py`
- [X] T016 [US1] Enforce listed-brand membership against candidate set in `src/lib/brand_list_classifier.py`
- [X] T017 [US1] Implement `new_brand` output with non-promoted `suggested_brand` in `src/lib/brand_list_classifier.py`
- [X] T018 [US1] Implement `no_brand` fallback rationale behavior in `src/lib/brand_list_classifier.py`
- [X] T019 [US1] Integrate candidate classification loop in `src/cli/classify_brand_list.py`

**Checkpoint**: Candidate rows classify correctly with deterministic category rules.

---

## Phase 4: User Story 2 - Filter Input by Existing Relevance Label (Priority: P1)

**Goal**: Keep all input rows in output while skipping LLM calls for true rows.

**Independent Test**: Run mixed input and verify true rows are present in output with `category=skipped` and required default fields.

### Tests for User Story 2

- [X] T020 [P] [US2] Add unit tests for true-like skip detection in `tests/unit/test_brand_list_classifier.py`
- [X] T021 [P] [US2] Add integration test for skip-row field contract in `tests/integration/test_cli_brand_list.py`

### Implementation for User Story 2

- [X] T022 [US2] Implement pre-filter decision path for true rows in `src/cli/classify_brand_list.py`
- [X] T023 [US2] Implement skipped-row defaults (`category`, brand fields, confidence, rationale) in `src/lib/brand_list_classifier.py`
- [X] T024 [US2] Ensure skipped rows bypass OpenRouter calls in `src/lib/classifier.py`
- [X] T025 [US2] Preserve all original input rows in final output writing path in `src/cli/classify_brand_list.py`

**Checkpoint**: Skip behavior is cost-safe and output-complete.

---

## Phase 5: User Story 3 - Preserve Existing Pipeline Behavior (Priority: P2)

**Goal**: Reuse existing OpenRouter and operational patterns from current workflow.

**Independent Test**: Verify new CLI behaves like current classifier for env var, model flag, batching, progress logs, and parse errors.

### Tests for User Story 3

- [X] T026 [P] [US3] Add integration test for CLI parity (`OPENROUTER_API_KEY`, model, batch/progress) in `tests/integration/test_cli_brand_list.py`
- [X] T027 [P] [US3] Add unit tests for OpenRouter response parsing reuse in `tests/unit/test_brand_list_classifier.py`

### Implementation for User Story 3

- [X] T028 [US3] Reuse existing OpenRouter client invocation path in `src/lib/classifier.py`
- [X] T029 [US3] Reuse existing batching/progress conventions in `src/cli/classify_brand_list.py`
- [X] T030 [US3] Reuse existing malformed-response error handling conventions in `src/lib/brand_list_classifier.py`
- [X] T031 [US3] Add candidate-row throughput benchmark hook in `scripts/benchmark.py`

**Checkpoint**: New workflow aligns with current operator expectations and runtime behavior.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, validation, and final hardening.

- [X] T032 [P] Update feature documentation and command examples in `README.md`
- [X] T033 [P] Update/validate quickstart instructions in `specs/002-brand-list-classifier/quickstart.md`
- [X] T034 Add integration regression for full-row output retention in `tests/integration/test_cli_brand_list.py`
- [X] T035 [P] Add unit regression for brand CSV header validation in `tests/unit/test_brand_list_classifier.py`
- [X] T036 Final cleanup/refactor for shared helpers in `src/lib/brand_list_classifier.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1 (Setup): starts immediately
- Phase 2 (Foundational): depends on Phase 1 and blocks all user stories
- Phases 3-5 (User Stories): depend on Phase 2 completion
- Phase 6 (Polish): depends on selected user stories being complete

### User Story Dependencies

- US1 (P1): starts after foundational tasks
- US2 (P1): starts after foundational tasks; can run in parallel with US1
- US3 (P2): starts after foundational tasks; validates parity across US1/US2 behavior

### Within Each User Story

- Tests first (write and fail)
- Implementation second
- Story-level validation checkpoint before advancing

### Parallel Opportunities

- Setup: T003-T005
- Foundational: T007-T010 after T006
- US1 tests: T012-T014
- US2 tests: T020-T021
- US3 tests: T026-T027
- Polish: T032-T033 and T035

---

## Parallel Example: User Story 1

```bash
Task: "Add unit tests for category validity and required fields in tests/unit/test_brand_list_classifier.py"
Task: "Add unit tests for brand-list prompt construction in tests/unit/test_brand_list_prompt_builder.py"
Task: "Add integration test for listed/new/no outcomes in tests/integration/test_cli_brand_list.py"
```

## Parallel Example: User Story 2

```bash
Task: "Add unit tests for true-like skip detection in tests/unit/test_brand_list_classifier.py"
Task: "Add integration test for skip-row field contract in tests/integration/test_cli_brand_list.py"
```

## Parallel Example: User Story 3

```bash
Task: "Add integration test for CLI parity in tests/integration/test_cli_brand_list.py"
Task: "Add unit tests for OpenRouter response parsing reuse in tests/unit/test_brand_list_classifier.py"
```

---

## Implementation Strategy

### MVP First (US1)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US1).
3. Validate US1 independently.

### Incremental Delivery

1. Deliver US1 category assignment.
2. Deliver US2 skip/output retention behavior.
3. Deliver US3 parity and reuse refinements.
4. Finish Phase 6 polish and docs.

### Validation Focus

1. True rows never trigger model calls.
2. Input row count equals output row count.
3. Candidate rows always get valid category output.
