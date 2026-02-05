# Feature Specification: Deeper Sentiment Analysis

**Feature Branch**: `004-deeper-sentiment-analysis`
**Created**: 2026-02-04
**Status**: Draft
**Input**: User description: "Additional pipeline option for deeper sentiment classification into Joy, Surprise, Anger, Disappointment, Excitement, and Neutral."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run deeper sentiment classification for one year (Priority: P1)

As a pipeline user, I can run a deep-sentiment command for a year and receive
JSON output containing tweet-level emotion classifications.

**Why this priority**: This is the core user-visible feature and delivers value
without requiring pipeline integration.

**Independent Test**: Run `python -m src.cli deep-sentiment --year 2024` and
verify JSON output under `sentiment/deep/<year>/` with required fields.

**Acceptance Scenarios**:

1. **Given** cleaned/process-ready tweet input for a year, **When** I run deep
   sentiment, **Then** output JSON includes one deterministic record per valid tweet.
2. **Given** repeated runs with identical inputs/config, **When** I run the same
   command twice, **Then** record ordering and predicted labels are identical.

---

### User Story 2 - Include deep sentiment in pipeline runs (Priority: P2)

As a pipeline user, I can optionally include deep sentiment during `run --all`
or year-scoped full runs without changing default pipeline behavior.

**Why this priority**: Keeps the current pipeline stable while making the new
capability easy to adopt.

**Independent Test**: Run `python -m src.cli run --year 2024 --all --with-deep-sentiment`
and verify standard stage outputs are unchanged and deep-sentiment artifacts are added.

**Acceptance Scenarios**:

1. **Given** a full-year run request with `--with-deep-sentiment`, **When** the
   pipeline finishes, **Then** deep-sentiment artifacts are present for that year.
2. **Given** a full-year run request without `--with-deep-sentiment`, **When**
   the pipeline finishes, **Then** no deep-sentiment artifacts are generated.

---

### User Story 3 - Support configurable model selection for deeper emotion labels (Priority: P3)

As a maintainer, I can select a BERTweet-compatible or better pretrained model
for deep emotion inference while enforcing the required six-label taxonomy.

**Why this priority**: Ensures long-term model flexibility without breaking
output contracts.

**Independent Test**: Run deep sentiment with explicit model override and verify
runtime validation either accepts compatible mappings or fails with clear errors.

**Acceptance Scenarios**:

1. **Given** a compatible checkpoint and mapping, **When** inference starts,
   **Then** labels resolve to only `joy|surprise|anger|disappointment|excitement|neutral`.
2. **Given** an incompatible checkpoint, **When** validation runs, **Then** the
   command fails before writing outputs.

---

### Edge Cases

- Input rows missing `tweet_id` or `text` are skipped with manifest counts.
- Tweets with no hashtags still produce an output record with empty hashtag list.
- Extremely long tweets are truncated deterministically via tokenizer settings.
- Model id2label values use mixed case/synonyms and require canonical mapping.
- Same tweet duplicated in input is handled deterministically (stable ordering).

## Requirements *(mandatory)*

### Constitutional Alignment *(mandatory)*

- Feature MUST preserve year-scoped isolation and MUST NOT mutate `data/raw`.
- Feature MUST be runnable independently and as an optional full-pipeline step.
- Feature MUST produce deterministic outputs and persist year-partitioned artifacts.
- Feature MUST document any memory constraints and use batching/chunking where needed.
- Feature MUST include README updates for command usage, model limits, and outputs.

### Functional Requirements

- **FR-001**: System MUST provide a CLI command for deep sentiment that accepts
  `--year` or `--data-dir` (and optional `--input-file`) as explicit inputs.
- **FR-002**: System MUST classify each valid tweet into exactly one of:
  `joy`, `surprise`, `anger`, `disappointment`, `excitement`, `neutral`.
- **FR-003**: System MUST output JSON records containing at minimum:
  `tweet_id`, `hashtags`, `text`, and `main_sentiment`.
- **FR-004**: System MUST write outputs under a year-scoped path
  `sentiment/deep/<year>/deep_sentiment.json`.
- **FR-005**: System MUST perform batch inference with configurable batch size
  and deterministic ordering.
- **FR-006**: System MUST validate model label mapping before inference and fail
  fast if required labels cannot be produced deterministically.
- **FR-007**: System MUST expose pipeline integration via an explicit optional
  run flag (for year and all-years full run modes) without altering defaults.
- **FR-008**: System MUST record manifest metadata including model id/version,
  invalid rows skipped, and output row counts.

### Key Entities *(include if feature involves data)*

- **DeepSentimentRecord**: Tweet-level JSON record with `tweet_id`, `hashtags`,
  `text`, and `main_sentiment`.
- **DeepSentimentManifest**: Run metadata containing model details, row counts,
  skipped-row counts, and output artifact path.
- **EmotionLabelMap**: Canonical mapping that resolves model labels into the
  six-label taxonomy required by this feature.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Two identical runs produce byte-identical deep-sentiment output
  files for the same year and config.
- **SC-002**: 100% of output records contain non-empty `tweet_id`, `text`, and
  `main_sentiment` in the required six-label set.
- **SC-003**: Deep-sentiment command processes a representative year dataset
  without OOM using configured batch size.
- **SC-004**: `run --all` and `run --year ... --all` include deep sentiment only
  when `--with-deep-sentiment` is explicitly provided.
