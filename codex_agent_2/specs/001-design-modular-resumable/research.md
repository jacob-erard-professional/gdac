# Phase 0 Research - Modular, Resumable NLP Analytics Pipeline

## Decision 1: Use Python 3.12 + Typer for CLI-first stage orchestration
- **Decision**: Implement CLI commands with Typer and stage execution modules in Python 3.12.
- **Rationale**: Fast implementation velocity, strong ecosystem for NLP/data tooling, and straightforward typed CLI ergonomics for single-stage and subset execution.
- **Alternatives considered**:
  - Go + Cobra: excellent binaries, but slower iteration for schema-heavy experimentation.
  - Rust + Clap: strong safety/performance, but higher MVP complexity for data tooling and agent integration.

## Decision 2: Artifact-first persistence on filesystem with versioned JSON/YAML contracts
- **Decision**: Store artifacts under `artifacts/` and persist manifest/stage records as JSON; maintain human-editable config and schema metadata in YAML.
- **Rationale**: Satisfies resumability/audit requirements without introducing DB complexity in MVP.
- **Alternatives considered**:
  - PostgreSQL metadata store: stronger querying but unnecessary setup overhead for MVP.
  - Object store only: good scale path but too much environment dependency for initial repository.

## Decision 3: Explicit dependency graph validation with no implicit upstream execution
- **Decision**: Represent stage dependencies declaratively (`StageDefinition`) and validate selected stage subsets before execution; never auto-run missing dependencies.
- **Rationale**: Matches constitutional stage isolation and avoids hidden side effects.
- **Alternatives considered**:
  - DAG auto-orchestration: convenient but violates no-implicit-execution constraint.

## Decision 4: Skip-completed behavior based on artifact existence + manifest terminal status
- **Decision**: A stage is skippable when all declared outputs exist with matching schema versions and latest stage run status is `succeeded`.
- **Rationale**: Protects against stale partial outputs and keeps skip semantics deterministic.
- **Alternatives considered**:
  - File existence only: too weak and can skip corrupted/incompatible outputs.
  - Manifest-only check: too weak if files were externally deleted.

## Decision 5: Isolate agent logic behind provider and workflow interfaces
- **Decision**: Core pipeline calls `HashtagNormalizerAgent` interface; concrete providers live under `src/agents/providers`.
- **Rationale**: Ensures core pipeline does not directly depend on LLM APIs and supports mock/no-op providers.
- **Alternatives considered**:
  - Direct SDK calls in stage logic: simpler at first but tightly coupled and hard to test.

## Decision 6: Agentic hashtag normalization artifact model
- **Decision**: Persist candidate hashtags, equivalence classes, mappings, confidence scores, and decision trace artifacts per iteration.
- **Rationale**: Enables iterative refinement, reproducibility, and auditability.
- **Alternatives considered**:
  - Only final mapping artifact: insufficient provenance for review and debugging.

## Decision 7: Human review hooks as state machine extension point (Future)
- **Decision**: Include lifecycle states (`draft`, `pending_review`, `approved`, `rejected`) in mapping records, but MVP automation only uses `draft` and optional threshold-based auto-accept.
- **Rationale**: Future-ready without blocking MVP delivery.
- **Alternatives considered**:
  - Omit review model entirely: blocks future compliance workflows.

## Decision 8: Determinism and non-determinism logging strategy
- **Decision**: Non-agent stages are deterministic by design. Agent stages log `provider`, `model`, `model_version`, `temperature`, `seed`, and prompt hash in execution records.
- **Rationale**: Meets constitution reproducibility requirements while acknowledging probabilistic behavior.
- **Alternatives considered**:
  - Force deterministic decoding only: may reduce semantic quality and flexibility.

## Decision 9: MVP vs Future scope boundaries
- **Decision**:
  - **MVP**: independent stage execution, subset execution, skip-completed behavior, artifact manifest, one hashtag agent loop.
  - **Future**: web UI for review, multi-agent adjudication, remote artifact store, scheduler/integration APIs.
- **Rationale**: Delivers minimal useful platform while preserving extension seams.
- **Alternatives considered**:
  - Include review UI in MVP: adds significant product scope and delays core platform validation.
