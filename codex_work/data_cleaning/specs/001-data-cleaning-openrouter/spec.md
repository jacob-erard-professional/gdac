# Feature Specification: Deterministic Twitter (X) Data Cleaning + OpenRouter Agents

**Feature Branch**: `001-data-cleaning-openrouter`
**Created**: 2026-02-09
**Status**: Draft
**Input**: User description: "Implement a deterministic, modular data cleaning repository for Twitter (X) CSV data containing a full tweet payload and a guessed `brand` association. Brand relevance classification MUST be performed using an agentic workflow backed by LLM inference via the OpenRouter API."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Deterministic Cleaning Pipeline (Priority: P1)

As a data engineer, I want to run a deterministic cleaning pipeline on raw Twitter (X)
CSV data so I get reproducible, auditable cleaned datasets with preserved columns.

**Why this priority**: Clean, deterministic data is the foundation for everything else.

**Independent Test**: Run the pipeline on a fixed CSV input and verify identical outputs
and manifests across repeated runs.

**Acceptance Scenarios**:

1. **Given** a raw CSV in `data/raw`, **When** I run the deterministic steps, **Then** I
   get normalized outputs in `data/intermediate` with manifests and structured logs.
2. **Given** the same input and config, **When** I re-run the pipeline, **Then** hashes and
   outputs are identical.

---

### User Story 2 - OpenRouter Agent Classification (Priority: P2)

As a data engineer, I want brand relevance classification performed by stateless LLM
agents via OpenRouter so I can flag whether tweet text is actually about the guessed
brand without overwriting the original value.

**Why this priority**: Brand relevance is required but must remain explicit and auditable.

**Independent Test**: Run classification on a deterministic, normalized input set and
confirm agent inputs/outputs are logged, hashed, cached, and schema-validated.

**Acceptance Scenarios**:

1. **Given** normalized inputs, **When** I invoke the classification step, **Then**
   agent inputs are hashed, prompts versioned, and model parameters logged.
2. **Given** cached outputs, **When** I re-run classification, **Then** results replay
   deterministically without re-calling the model.

---

### User Story 3 - CLI + Config Driven Operation (Priority: P3)

As a data engineer, I want to run individual steps or the full pipeline via CLI with
configurable models and thresholds so the system is flexible and reproducible.

**Why this priority**: Operations must be scriptable and config-driven.

**Independent Test**: Run a single step via CLI with custom input/output directories
and confirm manifests and logs are produced.

**Acceptance Scenarios**:

1. **Given** a step name and directories, **When** I run the CLI, **Then** only that
   step runs and outputs are written to the specified directory.

---

### Edge Cases

- What happens when `text` is empty or null?
- How does the system handle missing `brand` values?
- How does the system behave when OpenRouter is unavailable?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST preserve all original Twitter-provided columns byte-for-byte.
- **FR-002**: System MUST treat `brand` as a hypothesis and never overwrite it.
- **FR-003**: System MUST normalize and clean tweet `text` deterministically.
- **FR-004**: System MUST perform brand relevance classification via OpenRouter-backed agents.
- **FR-005**: System MUST produce auditable, reproducible artifacts with manifests.
- **FR-006**: System MUST implement a column registry and agent I/O schemas.
- **FR-007**: System MUST keep agents stateless, operating only on explicit inputs.
- **FR-008**: System MUST version prompts, log model parameters, hash inputs, and cache outputs.
- **FR-009**: System MUST support CLI execution for single steps and full pipeline runs.

### Constitutional Requirements

- **CR-001**: Pipeline behavior MUST be deterministic for the same input data and configuration.
- **CR-002**: Each cleaning concern MUST be a distinct, independently runnable step.
- **CR-003**: Steps MUST read exactly one input directory and write exactly one output directory.
- **CR-004**: Each step MUST produce a manifest and structured logs with row counts and rejections.
- **CR-005**: Raw data MUST remain read-only; outputs are new artifacts only.
- **CR-006**: Brand handling MUST preserve the original `brand` value and produce explicit flags or scores.
- **CR-007**: All thresholds and heuristics MUST live in configuration files, not code.

### Key Entities *(include if feature involves data)*

- **TweetRecord**: Raw tweet payload with `text`, guessed `brand`, and all original columns.
- **NormalizedText**: Deterministically normalized tweet `text` for stable agent inputs.
- **BrandNormalization**: Canonicalized brand label and alias mapping.
- **AgentInput**: Explicit input object passed to the LLM agent, including hashes.
- **AgentOutput**: Schema-validated response with relevance flag/score and rationale.
- **Manifest**: Input/output hashes, row counts, rejection counts, and step metadata.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Identical outputs and manifests across repeated runs with the same inputs.
- **SC-002**: 100% of agent calls log prompt version, model name, parameters, and input hash.
- **SC-003**: All steps emit structured logs with rows in/out and rejection counts.
- **SC-004**: CLI can run each step independently and the full pipeline end-to-end.
