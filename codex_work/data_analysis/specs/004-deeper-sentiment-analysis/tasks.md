# Tasks: Deeper Sentiment Analysis

**Input**: Design documents from `specs/004-deeper-sentiment-analysis/`
**Prerequisites**: plan.md (required), spec.md (required)

**Tests**: Include pytest coverage for deterministic output, label taxonomy
validation, CLI contract behavior, and optional pipeline integration.

**Organization**: Tasks are grouped by user story so each story is independently
implementable and testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Parallelizable task (different files, no dependency on incomplete tasks)
- **[Story]**: Story label (`[US1]`, `[US2]`, `[US3]`)
- Every task includes an exact file path

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Scaffold module/CLI integration points for deep sentiment.

- [X] T001 Create deep sentiment core module scaffold in `src/sentiment/deep_emotion.py`
- [X] T002 Create deep sentiment pipeline stage scaffold in `src/pipeline/stages/deep_sentiment.py`
- [X] T003 [P] Register CLI command wiring in `src/cli/main.py`
- [X] T004 [P] Add run-config fields for deep sentiment options in `src/pipeline/config.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish contracts, validation, and deterministic IO before stories.

**⚠️ CRITICAL**: Complete this phase before user story implementation.

- [X] T005 Define deep-sentiment input/output schema helpers in `src/sentiment/deep_emotion.py`
- [X] T006 Implement canonical six-label mapping + validation in `src/sentiment/deep_emotion.py`
- [X] T007 [P] Implement deterministic hashtag extraction utility in `src/sentiment/deep_emotion.py`
- [X] T008 [P] Implement stable JSON writer + manifest metadata emission in `src/sentiment/deep_emotion.py`
- [X] T009 Add foundational unit tests for schema and label mapping in `tests/unit/test_deep_sentiment_core.py`

**Checkpoint**: Foundation complete; story work can start.

---

## Phase 3: User Story 1 - Run deeper sentiment classification for one year (Priority: P1) 🎯 MVP

**Goal**: Run standalone deep sentiment classification and produce required JSON output.

**Independent Test**: Run `python -m src.cli deep-sentiment --year 2024` and
verify `sentiment/deep/2024/deep_sentiment.json` contains required fields.

### Tests for User Story 1

- [X] T010 [P] [US1] Add CLI argument validation tests in `tests/unit/test_cli_deep_sentiment.py`
- [X] T011 [US1] Add deterministic inference/output tests in `tests/unit/test_deep_sentiment_core.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement standalone CLI command in `src/cli/deep_sentiment.py`
- [X] T013 [US1] Implement batch inference runner with model loading and preprocessing in `src/sentiment/deep_emotion.py`
- [X] T014 [US1] Implement output writer with required fields (`tweet_id`, `hashtags`, `text`, `main_sentiment`) in `src/sentiment/deep_emotion.py`

**Checkpoint**: MVP command is independently runnable and deterministic.

---

## Phase 4: User Story 2 - Include deep sentiment in pipeline runs (Priority: P2)

**Goal**: Add optional orchestration hook for full-year/all-years runs.

**Independent Test**: Run `python -m src.cli run --year 2024 --all --with-deep-sentiment`
and verify deep-sentiment artifacts are produced in addition to normal outputs.

### Tests for User Story 2

- [X] T015 [US2] Add integration test for full-year pipeline mode with deep sentiment in `tests/integration/test_with_deep_sentiment_pipeline_mode.py`
- [X] T016 [P] [US2] Add integration test for all-years mode with deep sentiment in `tests/integration/test_with_deep_sentiment_pipeline_mode.py`

### Implementation for User Story 2

- [X] T017 [US2] Add `--with-deep-sentiment` and deep sentiment options to run command in `src/cli/run.py`
- [X] T018 [US2] Wire deep sentiment stage runner into orchestrator in `src/pipeline/orchestrator.py`
- [X] T019 [US2] Implement deep sentiment pipeline stage adapter in `src/pipeline/stages/deep_sentiment.py`

**Checkpoint**: Optional pipeline integration works without changing defaults.

---

## Phase 5: User Story 3 - Support configurable model selection and taxonomy validation (Priority: P3)

**Goal**: Support model override while enforcing required six-label taxonomy.

**Independent Test**: Run with supported and unsupported model IDs; verify pass/fail behavior.

### Tests for User Story 3

- [X] T020 [P] [US3] Add label-map compatibility tests in `tests/unit/test_deep_sentiment_core.py`
- [X] T021 [US3] Add CLI failure-path test for incompatible model mapping in `tests/unit/test_cli_deep_sentiment.py`

### Implementation for User Story 3

- [X] T022 [US3] Add model override and mapping-configuration support in `src/sentiment/deep_emotion.py`
- [X] T023 [US3] Add clear validation/error messages for incompatible label sets in `src/sentiment/deep_emotion.py`
- [X] T024 [US3] Document default model selection and override behavior in `README.md`

**Checkpoint**: Model flexibility is supported with strict taxonomy guarantees.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final quality, documentation, and compliance.

- [X] T025 [P] Add/refresh run-mode contract tests for deep sentiment integration in `tests/integration/test_pipeline_contract_responses.py`
- [X] T026 Add deterministic checksum coverage for deep sentiment outputs in `tests/integration/test_deterministic_rerun.py`
- [X] T027 Update README usage examples and output schema docs in `README.md`
- [X] T028 Run full test suite and record completion status in `specs/004-deeper-sentiment-analysis/tasks.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1 (Setup): starts immediately.
- Phase 2 (Foundational): depends on setup; blocks all user stories.
- Phase 3 (US1): depends on foundational completion.
- Phase 4 (US2): depends on US1 implementation for reusable core runner.
- Phase 5 (US3): depends on US1 core model loading and schema validation.
- Phase 6 (Polish): depends on desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: no dependency on other stories after Foundational.
- **US2 (P2)**: depends on US1 deep sentiment core command.
- **US3 (P3)**: depends on US1 model loader/validator implementation.

### Parallel Execution Examples

```bash
# Foundational parallel work
T006 + T007 + T008

# US1 parallel tests/implementation
T010 + T011, then T012 + T013

# US2 parallel tests
T015 + T016
```

## Implementation Strategy

### MVP First (US1)

1. Complete Phases 1-2.
2. Complete Phase 3 (US1).
3. Validate deterministic one-year deep sentiment output.

### Incremental Delivery

1. Ship standalone command (US1).
2. Add optional pipeline integration (US2).
3. Add model-flexibility hardening (US3).
4. Finish polish and documentation.
