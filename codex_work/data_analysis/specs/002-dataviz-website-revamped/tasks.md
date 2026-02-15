# Tasks: Dataset Comparison Visualization Website

**Input**: Design documents from `/home/jacoberard/agent_practice/gdac/codex_work/data_analysis/specs/002-dataviz-website-revamped/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish website workspace and baseline comparison app structure.

- [X] T001 Create website workspace directories `site/`, `site/src/`, `site/src/components/`, `site/src/lib/`, and `site/public/`
- [X] T002 Create frontend bootstrap files `site/package.json`, `site/vite.config.js`, `site/index.html`, and `site/src/main.jsx`
- [X] T003 [P] Create base application shell in `site/src/App.jsx` with placeholder regions for year selector, clouds, and tweet cards
- [X] T004 [P] Create shared styling tokens and layout styles in `site/src/styles.css`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build deterministic data-loading and normalization foundation used by all user stories.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T005 Implement year discovery requiring both dataset scopes in `site/src/lib/yearDiscovery.js`
- [X] T006 [P] Implement analytics JSON parsing helpers for `hashtag_frequency` and `parent_company_groups` in `site/src/lib/analyticsParsers.js`
- [X] T007 [P] Implement CSV parsing helpers for `celebrity_freq.csv` and raw brand aggregation in `site/src/lib/csvParsers.js`
- [X] T008 [P] Implement tweet normalization and dedupe helpers in `site/src/lib/tweetCardUtils.js`
- [X] T009 Implement contract-aligned API client methods (`listYears`, `getComparisonPayload`, `getTweetCardEntries`) in `site/src/lib/comparisonApiClient.js`
- [X] T010 Implement comparison orchestration service combining parsers and client in `site/src/lib/comparisonService.js`
- [X] T011 Implement shared widget status model (`loaded`, `partial`, `missing`) in `site/src/lib/statusModel.js`
- [X] T012 Add deterministic fixture data and validation script for loader smoke checks in `site/src/lib/__fixtures__/comparisonFixtures.json`

**Checkpoint**: Foundation ready; user stories can be implemented independently.

---

## Phase 3: User Story 1 - Select Year and Compare Sources (Priority: P1) 🎯 MVP

**Goal**: Users can select a year from the top dropdown, and the page loads only comparable years (both regular and full datasets).

**Independent Test**: With multiple fixture years, dropdown lists only years that have both `outputs/analytics/<year>` and `outputs/analytics/<year>_full`; changing year refreshes all views.

### Implementation for User Story 1

- [X] T013 [US1] Implement top year selector component in `site/src/components/YearSelector.jsx`
- [X] T014 [US1] Wire selected-year app state and reload flow in `site/src/App.jsx`
- [X] T015 [P] [US1] Implement dataset source badges/labels for regular and full scopes in `site/src/components/DatasetScopeHeader.jsx`
- [X] T016 [US1] Implement year eligibility filtering and no-years-available state in `site/src/lib/yearDiscovery.js`
- [X] T017 [US1] Add year-selection loading and error states in `site/src/components/EmptyState.jsx`
- [X] T018 [US1] Update root usage docs for year-selection behavior in `README.md`

**Checkpoint**: User Story 1 is independently functional and testable.

---

## Phase 4: User Story 2 - Review Required Word Clouds (Priority: P1)

**Goal**: Users see required word clouds for full hashtag+parent, celebrity (regular/full), and raw brand frequency (regular/full).

**Independent Test**: For a selected comparable year, all five required word clouds render with correctly scoped data and labels.

### Implementation for User Story 2

- [X] T019 [US2] Implement reusable word cloud renderer in `site/src/components/WordCloudPanel.jsx`
- [X] T020 [US2] Implement full combined hashtag+parent cloud mapping in `site/src/lib/comparisonService.js`
- [X] T021 [P] [US2] Implement regular/full celebrity cloud mapping in `site/src/lib/comparisonService.js`
- [X] T022 [P] [US2] Implement regular/full raw brand cloud mapping from raw `brand` column in `site/src/lib/comparisonService.js`
- [X] T023 [US2] Add word cloud section layout and side-by-side panels in `site/src/components/ComparisonCloudGrid.jsx`
- [X] T024 [US2] Wire all required cloud panels to app state in `site/src/App.jsx`
- [X] T025 [US2] Add per-widget missing/partial status messaging for cloud inputs in `site/src/components/WordCloudPanel.jsx`
- [X] T026 [US2] Document required cloud source files in `README.md`

**Checkpoint**: User Story 2 is independently functional and testable.

---

## Phase 5: User Story 3 - Browse Example Tweets (Priority: P2)

**Goal**: Users browse regular/full tweet-style cards with deduped text and arrow navigation; full card filters by `is_about_brand=false` (missing treated as false).

**Independent Test**: With duplicate and mixed-brand fixtures, both cards show unique text entries, arrows navigate index/total, and full scope applies filter semantics.

### Implementation for User Story 3

- [X] T027 [US3] Implement tweet-style display card component in `site/src/components/TweetCard.jsx`
- [X] T028 [US3] Implement dual-scope tweet card container with arrow controls in `site/src/components/TweetCardComparison.jsx`
- [X] T029 [P] [US3] Implement full-scope filter logic (`is_about_brand=false`, missing => false) in `site/src/lib/comparisonService.js`
- [X] T030 [P] [US3] Implement per-scope text dedupe integration in `site/src/lib/tweetCardUtils.js`
- [X] T031 [US3] Implement navigator state (`current_index`, `total_count`, arrow enable/disable) in `site/src/components/TweetCardComparison.jsx`
- [X] T032 [US3] Wire tweet card comparison section into application flow in `site/src/App.jsx`
- [X] T033 [US3] Add empty-state handling for no tweet entries in `site/src/components/TweetCardComparison.jsx`
- [X] T034 [US3] Document tweet-card filter and dedupe behavior in `README.md`

**Checkpoint**: User Story 3 is independently functional and testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final consistency, validation, and documentation quality across all stories.

- [X] T035 [P] Align all UI labels and canonical terms (`regular`, `full`, `year`) across `site/src/App.jsx` and `site/src/components/*`
- [X] T036 Add contract conformance checks for client payload shapes in `site/src/lib/comparisonApiClient.js`
- [X] T037 [P] Validate quickstart steps against implemented UI behavior in `specs/002-dataviz-website-revamped/quickstart.md`
- [X] T038 Run final documentation pass for new website workflow in `README.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies.
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks all stories.
- **Phase 3 (US1)**: Depends on Phase 2; recommended MVP slice.
- **Phase 4 (US2)**: Depends on Phase 2 and uses US1 year selection state.
- **Phase 5 (US3)**: Depends on Phase 2 and uses US1 year selection state.
- **Phase 6 (Polish)**: Depends on completion of selected user stories.

### User Story Dependency Graph

- **US1 (P1)**: Independent after foundational work.
- **US2 (P1)**: Independent after foundational work; can proceed after US1 state wiring is in place.
- **US3 (P2)**: Independent after foundational work; can proceed after US1 state wiring is in place.

Execution order: `US1 -> (US2 || US3) -> Polish`

### Parallel Opportunities

- **Setup**: `T003` and `T004` can run in parallel after `T001-T002`.
- **Foundational**: `T006`, `T007`, and `T008` can run in parallel.
- **US1**: `T015` can run in parallel with `T014`.
- **US2**: `T021` and `T022` can run in parallel after `T020`.
- **US3**: `T029` and `T030` can run in parallel after `T027-T028` scaffolding.
- **Polish**: `T035` and `T037` can run in parallel.

## Parallel Execution Examples

### User Story 2

```bash
# Parallelizable tasks for US2
Task: T021 in site/src/lib/comparisonService.js
Task: T022 in site/src/lib/comparisonService.js
```

### User Story 3

```bash
# Parallelizable tasks for US3
Task: T029 in site/src/lib/comparisonService.js
Task: T030 in site/src/lib/tweetCardUtils.js
```

## Implementation Strategy

### MVP First (US1)

1. Complete Phase 1 and Phase 2.
2. Deliver Phase 3 (US1) to enable year selection with strict comparable-year eligibility.
3. Validate independent test criteria for US1 before adding visualization complexity.

### Incremental Delivery

1. Add required word clouds (US2) as the first comparison payload expansion.
2. Add tweet-card comparison behavior (US3) with dedupe and navigation.
3. Finish with polish tasks for terminology, contract conformance, and docs.
