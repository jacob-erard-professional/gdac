# Tasks: Combining Sentiment with Parent Companies

**Input**: `specs/005-combining-sentiment-with-parent-companies/spec.md`
**Prerequisites**: plan.md (required), spec.md (required)

## Phase 1: Design + Contracts

- [ ] T001 Define input/output schema for parent-company sentiment joiner
  - Output fields: parent_company, counts, rates, net sentiment, confidence stats
- [ ] T002 Define join key strategy and mapping rules (tweet_id/year, brand/ad mapping)

## Phase 2: Implementation

- [ ] T003 Implement join + aggregation core (new module under `src/sentiment/` or `src/analytics/`)
- [ ] T004 Implement writer for joined parquet + summary JSON/CSV
- [ ] T005 Add CLI entrypoint (e.g., `parent-company-sentiment`)
- [ ] T006 Add pipeline stage adapter and flag wiring (`--with-parent-company-sentiment`)

## Phase 3: Tests

- [ ] T007 Unit tests for aggregation math and join coverage
- [ ] T008 Integration test for pipeline flag behavior

## Phase 4: Documentation

- [ ] T009 Update README with command usage and output artifacts

