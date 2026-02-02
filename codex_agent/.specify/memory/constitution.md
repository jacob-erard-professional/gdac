<!--
Sync Impact Report
- Version change: 1.0.2 -> 1.1.0
- Modified principles:
  - Added: VI. Year-Agnostic and Reusable Analytical Logic
- Added sections:
  - None
- Removed sections:
  - None
- Templates requiring updates:
  - ✅ updated: .specify/templates/plan-template.md
  - ✅ updated: .specify/templates/spec-template.md
  - ✅ updated: .specify/templates/tasks-template.md
  - ⚠ pending: .specify/templates/commands/*.md (directory not present in repository)
  - ✅ aligned: AGENTS.md
- Follow-up TODOs:
  - None
-->
# Social Media Data Analytics Pipeline Constitution

## Core Principles

### I. Modular Stage Separation and Code Quality
All pipeline code MUST be organized into explicit modules for ingestion, cleaning,
analysis, visualization, and reporting. Each stage MUST expose a clear interface,
MUST avoid cross-stage business logic leakage, and MUST pass linting, formatting, and
review checks before merge.
Rationale: strict stage boundaries reduce coupling, simplify maintenance, and prevent
hidden analytical errors.

### II. Reproducibility Through Parameterized Inputs
Runs across years MUST be driven by parameterized configuration (for example:
year range, platform, geography, filters, and model settings). Hardcoded time windows,
file paths, or platform-specific constants in pipeline logic are prohibited.
Rationale: parameterization enables reproducible reruns and reliable multi-year
comparisons.

### III. Stage-Level Data Validation and Logging
Each stage MUST validate inputs and outputs against defined schemas or quality rules,
MUST fail fast on critical violations, and MUST emit structured logs with traceable run
metadata. Logs MUST capture validation outcomes, row-level rejection counts, and
transformation summaries.
Rationale: observable, validated stages are required for trust in analytical outputs.

### IV. Methodological Transparency
Analytical assumptions, limitations, metric definitions, and methodological choices
MUST be documented alongside code and updated with every material change.
Documentation MUST distinguish observed facts from inferred conclusions.
Rationale: transparent methods support defensible interpretation and stakeholder trust.

### V. Testability, Performance, and Cross-Year Consistency
Analysis steps MUST be testable and repeatable through automated unit/integration tests
and deterministic execution settings. Large-dataset workloads MUST define and validate
performance budgets (runtime and memory). Standardized output schemas and metric
definitions MUST remain consistent across years unless a documented versioned change is
approved.
Rationale: stable, performant, and testable outputs are necessary for year-over-year
comparability.

### VI. Year-Agnostic and Reusable Analytical Logic
All analytical logic MUST be reusable across years without code modification.
Year-specific behavior MUST be driven by configuration and input data only. Hardcoded
year checks, year-specific branches, or one-off logic paths in analytics modules are
prohibited unless explicitly approved as a temporary exception.
Rationale: year-agnostic logic is required for scalable longitudinal analysis and
maintainable pipelines.

## Operational Standards

- Every pipeline run MUST produce a run manifest containing parameter values, code
  version, data snapshot identifiers, and output artifact locations.
- Data contracts for each stage MUST be versioned; breaking contract changes require a
  migration note and explicit reviewer approval.
- API contracts MUST be treated as logical interfaces and schemas, not as a requirement
  for a deployed HTTP service. Implementations MAY use internal interfaces or file-based
  contracts when they preserve the same contract semantics.
- Output datasets and reports MUST include year, source platform, and metric definition
  metadata to support longitudinal interpretation.
- Backfills or reruns MUST use the same parameter schema as production runs.

## Delivery Workflow and Quality Gates

- Plans, specs, and tasks MUST include an explicit Constitution Check against all six
  principles before implementation begins.
- Pull requests MUST include: test evidence, validation/logging evidence, performance
  impact statement, and documentation updates.
- Release readiness MUST be blocked if any required stage lacks validation, logging,
  reproducibility parameters, or cross-year comparability checks.
- Exceptions MUST be documented with an owner, expiry date, and remediation plan.

## Governance
This constitution is the highest project governance authority for pipeline delivery.
Amendments require: (1) a written proposal, (2) approval by project maintainers, and
(3) updates to impacted templates or workflows in the same change set.

Versioning policy follows semantic versioning:
- MAJOR: removal or incompatible redefinition of a principle or governance rule.
- MINOR: addition of a principle/section or material expansion of requirements.
- PATCH: clarifications that do not change required behavior.

Compliance review is mandatory at planning, pull request, and release checkpoints.
Non-compliance MUST be remediated before release unless a time-bound exception is
formally recorded.

**Version**: 1.1.0 | **Ratified**: 2026-02-01 | **Last Amended**: 2026-02-01
