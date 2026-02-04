# Feature Specification: Agentic Sentiment Analysis for X (Twitter) Data

**Feature Branch**: `002-agentic-sentiment-analysis`
**Created**: 2026-02-04
**Status**: Draft
**Input**: User description: "Build an agentic, multi-step sentiment analysis subsystem with strict JSON contracts and pipeline-safe integration."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run Agentic Sentiment from CLI (Priority: P1)

As an analyst, I run sentiment analysis independently for a year or explicit dataset
so I can generate auditable per-tweet sentiment outputs without running the full pipeline.

**Why this priority**: Independent CLI execution is the smallest usable delivery.

**Independent Test**: Run a sentiment command for one year and verify
`outputs/analytics/<year>/sentiment_agentic.jsonl` is created with valid records.

**Acceptance Scenarios**:

1. **Given** cleaned data for year 2024, **When** I run sentiment CLI for that year,
   **Then** one structured sentiment record is produced per input tweet.
2. **Given** `--data-dir` input for a year directory, **When** I run sentiment CLI,
   **Then** outputs are still written to deterministic year-scoped analytics paths.

---

### User Story 2 - Produce Multi-Agent, Supervised Sentiment Decisions (Priority: P2)

As a researcher, I use multiple specialized agents and a supervisor to obtain
final sentiment labels, confidence, and ambiguity flags.

**Why this priority**: This is the core analytical value of the subsystem.

**Independent Test**: Run sentiment on a small fixture and verify each output includes
normalizer, polarity, emotion, sarcasm, and supervisor-derived final fields.

**Acceptance Scenarios**:

1. **Given** input tweet text, **When** the workflow runs, **Then** each required
   agent emits strict JSON and the supervisor emits final sentiment.
2. **Given** conflicting agent signals, **When** the supervisor evaluates the record,
   **Then** confidence is calibrated and ambiguity flags are emitted when needed.

---

### User Story 3 - Integrate into Pipeline Without Breaking Baseline Behavior (Priority: P3)

As a maintainer, I can optionally include sentiment in the full pipeline while keeping
default pipeline behavior unchanged.

**Why this priority**: Protects existing workflows while enabling incremental adoption.

**Independent Test**: Run `run --year 2024 --all` with and without `--with-sentiment`
and verify baseline outputs are unchanged when the flag is absent.

**Acceptance Scenarios**:

1. **Given** full-pipeline run without sentiment flag, **When** I execute `--all`,
   **Then** baseline analytics outputs remain unchanged.
2. **Given** full-pipeline run with sentiment flag, **When** I execute `--all --with-sentiment`,
   **Then** sentiment artifacts are added under year-scoped output paths.

---

### Edge Cases

- Malformed JSON returned by any LLM step.
- Missing required upstream artifacts (`cleaned.csv` / tweet id / text).
- Rate-limit and transient provider errors.
- Non-English or slang-heavy tweets.
- Sarcasm signals contradict polarity/emotion signals.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Subsystem MUST be invokable independently by CLI for `--year` or `--data-dir`.
- **FR-002**: Subsystem MUST write deterministic outputs under `outputs/analytics/<year>/`.
- **FR-003**: Required agents MUST include normalizer, polarity, emotion, sarcasm, and supervisor.
- **FR-004**: Each agent MUST emit strict machine-parseable JSON.
- **FR-005**: Supervisor MUST produce final sentiment (`positive|neutral|negative`) and confidence (`0.0-1.0`).
- **FR-006**: Output records MUST include per-agent payloads and flags for ambiguity/low confidence.
- **FR-007**: Agent execution SHOULD parallelize independent steps where applicable.
- **FR-008**: LLM usage MUST support OpenRouter-compatible models with per-agent model selection.
- **FR-009**: Integration into full pipeline MUST be opt-in (e.g., `--with-sentiment`) and off by default.
- **FR-010**: Subsystem MUST NOT write to `data/raw/` and MUST preserve year isolation.
- **FR-011**: README MUST document roles, models, CLI usage, limitations, and cost controls.

### Key Entities *(include if feature involves data)*

- **SentimentRunRequest**: execution mode, year/data_dir, model config, and flags.
- **AgentModelConfig**: model id and runtime controls per agent.
- **NormalizerOutput**: normalized text and transformation metadata.
- **PolarityOutput**: sentiment label, confidence, and rationale.
- **EmotionOutput**: fixed-taxonomy emotion label, confidence, and rationale.
- **SarcasmOutput**: sarcasm flag, confidence, and rationale.
- **SupervisorOutput**: final sentiment decision, calibrated confidence, and flags.
- **SentimentRecord**: full per-tweet output contract combining all agent outputs.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Sentiment CLI run writes deterministic artifacts for the selected year.
- **SC-002**: Every output record conforms to schema and includes all required agent fields.
- **SC-003**: Supervisor emits final sentiment and confidence for 100% of processed tweets.
- **SC-004**: Pipeline default run behavior remains unchanged unless sentiment flag is provided.
- **SC-005**: Raw files remain unchanged after any sentiment run.
- **SC-006**: README reflects implemented sentiment workflow and operational constraints.
