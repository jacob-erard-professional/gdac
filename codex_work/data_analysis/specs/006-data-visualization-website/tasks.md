# Tasks: Data Visualization Website

**Input**: Design documents from `/specs/006-data-visualization-website/`
**Prerequisites**: plan.md (required), spec.md (required for user stories),
research.md, data-model.md, contracts/

**Tests**: Include tests when required to prove determinism, data contract
validity, or correct rendering of required outputs.

**Organization**: Tasks are grouped by user story to enable independent
implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- Data MUST remain year-scoped under `data/*/<year>/`
- Raw input path is read-only: `data/raw/<year>/`
- Derived outputs are written under `outputs/analytics/<year>/` and `outputs/aux/<year>/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish repository structure and frontend scaffolding

- [ ] T001 Create `site/` directory structure (`site/`, `site/src/`, `site/public/`)
- [ ] T002 [P] Add base build tooling (Vite or equivalent) in `site/`
- [ ] T003 [P] Add shared config for year selection + output roots in `site/src/data/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Data loaders + contracts required before user stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement data contracts for required artifacts in `site/src/data/contracts.ts`
- [ ] T005 [P] Implement JSON/CSV loaders in `site/src/data/loaders.ts`
- [ ] T006 [P] Implement optional-artifact detection + empty states
- [ ] T007 Add year discovery (based on `outputs/analytics/`) in `site/src/data/years.ts`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Overview (Priority: P1) 🎯 MVP

**Goal**: Year-level overview with core analytics and navigation

**Independent Test**: Load site locally and confirm overview renders when only
`hashtags_frequency.json` and `mentions_frequency.json` are available.

### Implementation for User Story 1

- [ ] T008 [P] [US1] Build year selector + routing in `site/src/pages/`
- [ ] T009 [US1] Add hashtag/mention frequency charts in `site/src/components/`
- [ ] T010 [US1] Add download links for analytics files
- [ ] T011 [US1] Update `site/README.md` with local run steps

**Checkpoint**: User Story 1 is independently functional and testable

---

## Phase 4: User Story 2 - Sentiment Dashboards (Priority: P2)

**Goal**: Visualize sentiment + parent company sentiment outputs

**Independent Test**: Load site with `ad_sentiment_summary.json` and
`parent_company_sentiment_summary.json` and confirm charts render.

### Implementation for User Story 2

- [ ] T012 [P] [US2] Add ad sentiment summary charts
- [ ] T013 [US2] Add parent company sentiment summary + time slices
- [ ] T014 [US2] Wire links to raw JSON/CSV downloads
- [ ] T015 [US2] Update root `README.md` with visualization steps

**Checkpoint**: User Stories 1 and 2 both work independently

---

## Phase 5: User Story 3 - Deep Emotion Dashboards (Priority: P3)

**Goal**: Visualize deep sentiment + emotion breakdown outputs

**Independent Test**: Load site with deep sentiment and breakdown JSONs and
confirm charts render without errors.

### Implementation for User Story 3

- [ ] T016 [P] [US3] Add deep sentiment summary + time slice charts
- [ ] T017 [US3] Add parent/brand emotion breakdown charts
- [ ] T018 [US3] Verify optional aux outputs show graceful empty states

**Checkpoint**: All user stories are independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T019 [P] Add responsive layout polish in `site/src/styles/`
- [ ] T020 Finalize visual design tokens and theming
- [ ] T021 [P] Add smoke test script for local rendering
- [ ] T022 Conduct data contract validation on sample year outputs
- [ ] T023 Run quickstart validation + README final pass

