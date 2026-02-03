---
description: "Task list template for feature implementation"
---

# Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`
**Prerequisites**: plan.md (required), spec.md (required for user stories),
research.md, data-model.md, contracts/

**Tests**: Include tests when requested in spec or when required to prove
constitution compliance (determinism, stage isolation, raw immutability).

**Organization**: Tasks are grouped by user story to enable independent
implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Data MUST remain year-scoped under `data/*/<year>/`
- Raw input path is read-only: `data/raw/<year>/`
- Derived outputs are written only under year-scoped processed/enriched/analytics paths
- Paths shown below assume a single-project CLI pipeline

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish repository structure and CLI scaffolding

- [ ] T001 Create/verify year-scoped directories under `data/`
- [ ] T002 Implement CLI argument parsing for `--year` and `--data-dir`
- [ ] T003 [P] Add deterministic configuration handling (seed, sort/order, stable output)
- [ ] T004 [P] Add safeguards preventing writes to `data/raw/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Pipeline foundations required before user stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Implement stage contracts for `ingest`, `clean`, `process`, `analyze`,
  optional `visualize`, and `export`
- [ ] T006 [P] Implement explicit input/output artifact definitions per stage
- [ ] T007 [P] Implement chunked/streaming data loading where applicable
- [ ] T008 Add intermediate artifact persistence strategy
- [ ] T009 Add per-year output isolation checks to prevent cross-year overwrite
- [ ] T010 Add integration test proving single-stage and full-pipeline execution modes

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - [Title] (Priority: P1) 🎯 MVP

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement story-specific pipeline logic in appropriate stage module
- [ ] T012 [US1] Add deterministic test coverage for story outputs
- [ ] T013 [US1] Add year-scoped artifact output validation
- [ ] T014 [US1] Update README documentation for new capability

**Checkpoint**: User Story 1 is independently functional and testable

---

## Phase 4: User Story 2 - [Title] (Priority: P2)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Implementation for User Story 2

- [ ] T015 [P] [US2] Implement story-specific analytics/time/event/text logic
- [ ] T016 [US2] Add test coverage for stage-level rerun and artifact persistence
- [ ] T017 [US2] Verify memory-safe handling on representative large input slices
- [ ] T018 [US2] Update README documentation for new capability

**Checkpoint**: User Stories 1 and 2 both work independently

---

## Phase 5: User Story 3 - [Title] (Priority: P3)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Implementation for User Story 3

- [ ] T019 [P] [US3] Implement remaining feature scope
- [ ] T020 [US3] Add compliance tests for raw immutability and cross-year isolation
- [ ] T021 [US3] Validate CLI behavior for single-stage, single-year full, and all-years full runs
- [ ] T022 [US3] Update README documentation for new capability

**Checkpoint**: All user stories are independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T023 [P] Consolidate and optimize chunked/streaming performance
- [ ] T024 Finalize analytics output schema/version notes
- [ ] T025 [P] Add/refresh integration tests for end-to-end reproducibility
- [ ] T026 Conduct constitution compliance review and record evidence
- [ ] T027 Run quickstart/usage validation and README final pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: Depend on Foundational completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### Within Each User Story

- Determinism and artifact-path tests before final merge
- Stage implementation before CLI wiring for that story
- README update required before marking story complete

### Parallel Opportunities

- Setup tasks marked [P] can run in parallel
- Foundational tasks marked [P] can run in parallel
- Once Foundational completes, user stories can proceed in parallel by team capacity

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should remain independently completable and testable
- Do not add tasks that write to `data/raw/`
- Commit after each task or logical group
