---

description: "Task list template for feature implementation"
---

# Tasks: Brand Mention Classifier Prompt

**Input**: Design documents from `/specs/001-brand-mention-classifier/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are REQUIRED unless the feature specification explicitly documents a waiver with rationale.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan in src/ and tests/
- [X] T002 Add Python packaging metadata in pyproject.toml
- [X] T003 [P] Add base README section for this feature in README.md
- [X] T004 [P] Add initial CLI module scaffold in src/cli/classify_brand_mentions.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Define data schemas in src/models/schemas.py
- [X] T006 Implement CSV input/output utilities in src/lib/csv_io.py
- [X] T007 Implement OpenRouter client wrapper in src/lib/openrouter_client.py
- [X] T008 Implement prompt template builder in src/lib/prompt_builder.py
- [X] T009 Implement response parsing/validation in src/lib/response_parser.py
- [X] T010 Wire environment variable validation for `OPENROUTER_API_KEY` in src/lib/config.py
- [X] T011 Implement JSON-like column parsing with safe fallback in src/lib/csv_io.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Classify Brand Mentions (Priority: P1) MVP

**Goal**: Classify whether a tweet is about its assigned brand using the LLM

**Independent Test**: Run a small CSV through the core classification function
and verify `is_about_brand` outputs match expected labels.

### Tests for User Story 1 (REQUIRED unless explicitly waived)

- [X] T012 [P] [US1] Unit test prompt composition in tests/unit/test_prompt_builder.py
- [X] T013 [P] [US1] Unit test response parsing in tests/unit/test_response_parser.py
- [X] T014 [P] [US1] Unit test classifier core in tests/unit/test_classifier.py

### Implementation for User Story 1

- [X] T015 [US1] Implement classifier core using prompt + OpenRouter in src/lib/classifier.py
- [X] T016 [US1] Add primary signal weighting for `text` in src/lib/prompt_builder.py
- [X] T017 [US1] Add secondary context inclusion for other columns in src/lib/prompt_builder.py

**Checkpoint**: User Story 1 classification works with in-memory inputs

---

## Phase 4: User Story 2 - Provide Rationale & Confidence (Priority: P2)

**Goal**: Include rationale and confidence in all outputs

**Independent Test**: Run the classifier on a sample row and verify rationale
and confidence fields are populated and validated.

### Tests for User Story 2 (REQUIRED unless explicitly waived)

- [X] T018 [P] [US2] Unit test confidence and rationale validation in tests/unit/test_response_parser.py
- [X] T019 [P] [US2] Unit test rationale presence in tests/unit/test_classifier.py

### Implementation for User Story 2

- [X] T020 [US2] Extend response schema to require rationale and confidence in src/models/schemas.py
- [X] T021 [US2] Enforce rationale/confidence extraction in src/lib/response_parser.py
- [X] T022 [US2] Update classifier output to include rationale/confidence in src/lib/classifier.py

**Checkpoint**: User Story 2 outputs rationale and confidence for every row

---

## Phase 5: User Story 3 - Batch Output (Priority: P3)

**Goal**: Provide batch CSV/JSONL output through the CLI

**Independent Test**: Run the CLI with input/output paths and verify the output
file includes classification fields.

### Tests for User Story 3 (REQUIRED unless explicitly waived)

- [X] T023 [P] [US3] Integration test CLI batch CSV in tests/integration/test_cli_batch.py
- [X] T024 [P] [US3] Integration test CLI JSONL output in tests/integration/test_cli_batch.py

### Implementation for User Story 3

- [X] T025 [US3] Implement CLI argument parsing (`--input`, `--output`, `--format`, `--model`) in src/cli/classify_brand_mentions.py
- [X] T026 [US3] Implement batch CSV read/write flow in src/lib/csv_io.py
- [X] T027 [US3] Implement JSONL output option in src/lib/csv_io.py
- [X] T028 [US3] Wire CLI to classifier core in src/cli/classify_brand_mentions.py

**Checkpoint**: User Story 3 produces batch outputs in CSV and JSONL

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T029 [P] Update README with current functionality and run instructions in README.md
- [X] T030 [P] Add CLI usage examples in README.md
- [X] T031 Add quick performance benchmark script in scripts/benchmark.py
- [X] T032 [P] Add error handling for missing/empty `text` or `brand` in src/lib/classifier.py
- [X] T033 [P] Add logging for batch processing in src/cli/classify_brand_mentions.py
- [X] T034 [P] Add per-row progress logging in src/cli/classify_brand_mentions.py
- [X] T035 [P] Add batch-size support for streaming processing in src/cli/classify_brand_mentions.py
- [X] T036 [P] Switch OpenRouter calls to batch-of-100 TOON inputs with JSON schema enforcement

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can proceed in parallel after Phase 2
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2)
- **User Story 2 (P2)**: Depends on User Story 1 classifier outputs
- **User Story 3 (P3)**: Depends on User Story 1 classifier outputs

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before CLI integration
- Story complete before moving to next priority

### Parallel Opportunities

- Setup tasks marked [P] can run in parallel
- Foundational tasks T006-T010 can run in parallel
- Within each story, tests and model tasks marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch prompt composition and parsing tests together:
Task: "Unit test prompt composition in tests/unit/test_prompt_builder.py"
Task: "Unit test response parsing in tests/unit/test_response_parser.py"

# Launch classifier core test in parallel once scaffolding exists:
Task: "Unit test classifier core in tests/unit/test_classifier.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently

### Incremental Delivery

1. Complete Setup + Foundational -> Foundation ready
2. Add User Story 1 -> Test independently -> MVP
3. Add User Story 2 -> Test independently
4. Add User Story 3 -> Test independently
5. Apply polish tasks, update README
