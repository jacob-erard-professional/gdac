# Feature Specification: Brand List Classifier

**Feature Branch**: `[002-brand-list-classifier]`  
**Created**: 2026-02-13  
**Status**: Draft  
**Input**: User description: "Create a plan for brand-list-classifier that reuses as much code as possible from the data_cleaning directory. I want the workflow to take in a csv, remove all the rows that have the value true in its is_about_brand column, and then run the LLM prompting via openrouter, exactly like the brand relevance workflow."

## Clarifications

### Session 2026-02-13

- Q: Should rows filtered out (`is_about_brand = true`) appear in output? -> A: Yes, keep all input rows in output and skip classification for true rows.
- Q: What is the authoritative input method for candidate brand list? -> A: Provide a one-column CSV file.
- Q: How should `new_brand` be handled in output? -> A: Keep `new_brand` + `suggested_brand` without auto-promoting to assigned brand.
- Q: Should brand list CSV require a header row? -> A: Yes, require a `brand` header.
- Q: What values should skipped-row classification fields contain? -> A: Use `category=skipped`, empty brand fields, `confidence=0`, and explicit skip rationale.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Classify Candidate Tweets by Brand (Priority: P1)

As a data analyst, I want to classify tweets against a candidate brand list so I
can assign each tweet to a specific brand category.

**Why this priority**: This is the core value of the feature and replaces the
single-brand relevance decision with multi-brand routing.

**Independent Test**: Provide a CSV with `is_about_brand = false` rows and a
brand list, then verify each processed row returns one of: listed brand,
`new_brand`, or `no_brand`.

**Acceptance Scenarios**:

1. **Given** a tweet that clearly matches a brand in the provided list,
   **When** classification runs, **Then** output `assigned_brand` is that brand.
2. **Given** a tweet that does not match any listed brand but indicates another
   clear brand, **When** classification runs, **Then** output `assigned_brand`
   is `new_brand` and includes `suggested_brand`.
3. **Given** a tweet unrelated to brands, **When** classification runs,
   **Then** output `assigned_brand` is `no_brand`.

---

### User Story 2 - Filter Input by Existing Relevance Label (Priority: P1)

As an operator, I want the workflow to skip rows with `is_about_brand = true`
so the model only spends tokens on rows that still need brand assignment.

**Why this priority**: This enforces the desired workflow and controls cost.

**Independent Test**: Run on a mixed CSV and verify only rows where
`is_about_brand` is false are sent to classification.

**Acceptance Scenarios**:

1. **Given** an input CSV with mixed values in `is_about_brand`, **When** the
   workflow runs, **Then** only false rows are classified.

---

### User Story 3 - Preserve Existing Pipeline Behavior (Priority: P2)

As a maintainer, I want to reuse existing OpenRouter prompting flow and IO
patterns so this feature is simple to maintain and test.

**Why this priority**: Reuse reduces regression risk and delivery time.

**Independent Test**: Confirm CLI flags, environment variable behavior,
error-handling style, and output format conventions align with the existing
brand relevance workflow.

**Acceptance Scenarios**:

1. **Given** existing runbooks and operator habits, **When** the new workflow is
   executed, **Then** usage is consistent with the current classifier patterns.

### Edge Cases

- `is_about_brand` column missing from input CSV
- `is_about_brand` values use mixed encodings (`false`, `False`, `0`, empty)
- brand list is empty
- LLM output cannot be parsed
- tweet text is missing or empty

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept CSV input containing `text` and
  `is_about_brand` columns.
- **FR-002**: System MUST filter out all rows where `is_about_brand` is true
  before sending rows to classification.
- **FR-003**: System MUST classify each remaining row as one of:
  `listed_brand`, `new_brand`, or `no_brand`.
- **FR-004**: For `listed_brand`, system MUST output the selected brand from the
  provided list.
- **FR-005**: For `new_brand`, system MUST output a `suggested_brand` value.
- **FR-005a**: For `new_brand`, system MUST NOT auto-promote `suggested_brand`
  into `assigned_brand`; it remains a suggestion for downstream review.
- **FR-006**: For `no_brand`, system MUST output a rationale indicating why no
  brand assignment was made.
- **FR-007**: System MUST run prompting through OpenRouter using the same API key
  environment variable strategy as the current workflow.
- **FR-008**: CLI MUST allow model selection via argument.
- **FR-009**: Workflow MUST reuse existing parsing, prompting, and IO components
  where behavior is equivalent.
- **FR-010**: System MUST write output rows with original columns plus
  classification fields.
- **FR-012**: Candidate brands MUST be loaded from a CSV file containing exactly
  one brand-name column.
- **FR-013**: Brand list CSV MUST include a header row named `brand`.
- **FR-011**: Rows with `is_about_brand = true` MUST be preserved in the output
  file and marked as skipped from brand-list classification.
- **FR-014**: Rows skipped from classification MUST set `category=skipped`,
  `assigned_brand=""`, `suggested_brand=""`, `confidence=0`, and rationale
  `Skipped: already is_about_brand=true`.

### Key Entities *(include if feature involves data)*

- **BrandCandidateSet**: Input list of known brand names for assignment.
- **TweetCandidate**: Row eligible for brand-list classification (`is_about_brand`
  false).
- **BrandListClassificationResult**: Output category (`listed_brand`,
  `new_brand`, `no_brand`, `skipped`), assigned/suggested brand, confidence,
  rationale.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of rows with `is_about_brand = false` receive one valid
  classification category.
- **SC-002**: 100% of rows with `is_about_brand = true` are excluded from LLM
  calls.
- **SC-006**: 100% of input rows are present in output rows (no row loss), with
  true rows explicitly indicated as skipped from classification.
- **SC-003**: Batch run for 10,000-row input completes within existing workflow
  operational tolerance (no worse than 20% increase over current baseline).
- **SC-004**: At least 95% of classified rows include a non-empty rationale.
- **SC-005**: Operators can run the workflow using the documented CLI in under
  5 minutes without code changes.
