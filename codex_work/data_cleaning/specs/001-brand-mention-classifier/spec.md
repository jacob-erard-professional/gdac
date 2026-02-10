# Feature Specification: Brand Mention Classifier Prompt

**Feature Branch**: `[001-brand-mention-classifier]`  
**Created**: 2026-02-10  
**Status**: Draft  
**Input**: User description: "I want to create a very simple LLM prompt that takes in twitter data as a CSV, plus a brand column, and decides whether or not the tweet is actually talking about the brand it was assigned. The main deciding factor should be the text, but the other columns should provide some meaning in case"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Classify Brand Mentions (Priority: P1)

As a data analyst, I upload a CSV of tweets with a `brand` column and receive a
classification indicating whether each tweet is actually about the assigned
brand.

**Why this priority**: This is the core value of the feature and enables
downstream brand analytics.

**Independent Test**: Provide a small CSV with known examples and verify that
the output includes `is_about_brand` for every row with correct values.

**Acceptance Scenarios**:

1. **Given** a CSV row with text that clearly mentions the assigned brand, **When**
   the classifier runs, **Then** the output marks `is_about_brand = true`.
2. **Given** a CSV row where the brand name appears in an unrelated context,
   **When** the classifier runs, **Then** the output marks
   `is_about_brand = false`.

---

### User Story 2 - Provide Rationale & Confidence (Priority: P2)

As an analyst, I want a brief rationale and confidence score so I can audit
borderline cases without rereading all tweets.

**Why this priority**: Human review is required for ambiguous or high-impact
brands.

**Independent Test**: Run the classifier on a known ambiguous row and verify the
output includes `rationale` and `confidence` fields.

**Acceptance Scenarios**:

1. **Given** an ambiguous tweet, **When** classification runs, **Then** the
   output includes a concise rationale and a confidence score.

---

### User Story 3 - Batch Output (Priority: P3)

As an operator, I want a batch mode that produces a CSV/JSONL output file so I
can integrate with existing pipelines.

**Why this priority**: Batch-friendly output is needed for scheduled data
processing.

**Independent Test**: Run the CLI with input and output paths and confirm the
output file is created with expected columns.

**Acceptance Scenarios**:

1. **Given** input and output paths, **When** the CLI runs, **Then** a new output
   file is produced with classification fields appended.

---

### Edge Cases

- What happens when `text` is empty or missing?
- How does the system handle brand names that are common words?
- What happens when the tweet mentions multiple brands?
- How does the system handle non-English text?
- How does the system handle JSON-encoded columns like `referenced_tweets` and
  `entities.annotations` when they are missing or malformed?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a CSV input with required columns `text` and
  `brand`.
- **FR-002**: System MUST treat `text` as the primary signal and use other
  columns only for disambiguation.
- **FR-002a**: System MUST parse JSON-encoded columns when present, but MUST
  tolerate missing or malformed values by treating them as empty.
- **FR-003**: System MUST output a boolean `is_about_brand` for every input row.
- **FR-004**: System MUST include optional `confidence` and `rationale` fields
  for every output row.
- **FR-005**: Users MUST be able to run the classifier in batch mode and write
  results to an output file.
- **FR-006**: System MUST use OpenRouter for LLM prompting and read the API key
  from an exported environment variable.
- **FR-007**: CLI MUST accept a `--model` option to select the OpenRouter model.
- **FR-008**: If `text` or `brand` is missing/empty, the system MUST return
  `is_about_brand = false` with a rationale indicating missing input.
- **FR-009**: Numeric metrics fields MUST treat missing values as `0`.

*Example of marking unclear requirements:*

- **FR-010**: System MUST support optional JSONL output format via a CLI flag.

### Key Entities *(include if feature involves data)*

- **TweetRecord**: Source tweet text, assigned brand, and optional metadata
  columns.
- **ClassificationResult**: Output fields `is_about_brand`, `confidence`, and
  `rationale` tied to a tweet record.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of input rows produce an output row with `is_about_brand`.
- **SC-002**: Batch processing completes for 10k rows in under 2 minutes on a
  standard laptop (measured locally).
- **SC-003**: 95% of rows produce a non-empty rationale string.
- **SC-004**: `README.md` reflects all available functionality and how to run it.

### Non-Functional Requirements

- **NFR-001**: System MUST meet the batch performance target in SC-002.
- **NFR-002**: Any non-Python component MUST include a performance justification.
- **NFR-003**: All outputs and generated artifacts MUST remain within the
  repository (temporary files may use `/tmp`).
- **NFR-004**: `README.md` MUST describe all existing functionality and how to
  run it.
