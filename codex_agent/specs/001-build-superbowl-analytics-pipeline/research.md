# Research: Super Bowl X Analytics Pipeline

## Decision 1: Modular stage contract pattern

- **Decision**: Implement stage modules as independent Python packages with a shared
  stage interface (`run(input_ref, config, context) -> stage_result`).
- **Rationale**: Enforces strict separation of ingestion, cleaning, enrichment,
  analysis, visualization, and reporting while allowing orchestrated execution.
- **Alternatives considered**:
  - Monolithic script with internal functions (rejected: weak separation, harder testing)
  - Workflow engine-first design (rejected for initial scope complexity)

## Decision 2: Configuration-first execution

- **Decision**: Use YAML configuration files for event windows, keyword groups, KPI
  definitions, and data quality thresholds; CLI passes `--event` and `--year`.
- **Rationale**: Supports reproducibility and avoids hardcoded values while enabling
  consistent reruns across years.
- **Alternatives considered**:
  - Hardcoded constants in code (rejected: violates constitution reproducibility rule)
  - Database-only configuration (rejected: adds operational overhead for early phase)

## Decision 3: Data integrity with layered storage

- **Decision**: Store raw, cleaned, and processed data in separate top-level partitions
  with immutable raw snapshots and versioned manifests.
- **Rationale**: Preserves source integrity, improves auditability, and simplifies
  rollback/reprocessing.
- **Alternatives considered**:
  - Single mutable dataset path (rejected: poor lineage and integrity guarantees)
  - Full data warehouse upfront (rejected: unnecessary for initial pipeline scope)

## Decision 4: Validation and logging standard

- **Decision**: Apply schema validation at every stage boundary and emit structured JSON
  logs including row counts, rejection counts, validation failures, and timings.
- **Rationale**: Provides traceability and fast diagnosis for messy social media data.
- **Alternatives considered**:
  - Logging only at orchestrator level (rejected: insufficient per-stage observability)
  - Freeform text logs (rejected: weak machine-readability and aggregation)

## Decision 5: KPI comparability across years

- **Decision**: Maintain canonical KPI definition files with explicit formula versioning
  and attach `kpi_definition_version` to all KPI outputs.
- **Rationale**: Enables rigorous year-over-year comparison and controlled metric changes.
- **Alternatives considered**:
  - Ad hoc KPI edits per year (rejected: breaks comparability)
  - Embedding formulas only in code comments (rejected: poor governance)

## Decision 6: Orchestrator interface and automation contract

- **Decision**: Provide a CLI-first orchestrator and a minimal REST contract for
  triggering runs and retrieving artifacts for automation/reporting workflows.
- **Rationale**: Meets direct CLI usability needs while supporting downstream tooling.
- **Alternatives considered**:
  - CLI-only, no service contract (rejected: limits integration/automation options)
  - API-only, no CLI (rejected: conflicts with operator workflow requirement)
