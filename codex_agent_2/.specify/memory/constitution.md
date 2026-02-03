<!--
Sync Impact Report
- Version change: 1.0.0 -> 1.0.1
- Modified principles:
  - III. Agentic Workflows for Semantic Tasks (added minimum workflow definition)
- Modified sections:
  - Operational Requirements (added validation error schema and data retention/privacy policy)
  - Governance (clarified this amendment as PATCH-level)
- Removed sections: None
- Templates requiring updates:
  - ✅ .specify/templates/plan-template.md
  - ✅ .specify/templates/spec-template.md
  - ✅ .specify/templates/tasks-template.md
- Runtime docs status:
  - ℹ No README.md or docs/quickstart.md present in repository; no update required
- Follow-up TODOs:
  - None
-->
# Modular, Resumable, Agentic NLP Pipeline Constitution

## Core Principles

### I. Pipeline Modularity & Resumability
Every pipeline stage MUST be runnable independently via CLI, MUST NOT implicitly
trigger upstream stages, MUST accept explicit input artifact paths, MUST produce explicit
output artifacts, and MUST be idempotent when re-run with identical inputs. Rationale:
independent and resumable execution limits blast radius and enables reliable recovery.

### II. Artifact-Centric Design
All intermediate outputs MUST be persisted as versioned artifacts. No stage may rely on
in-memory state from previous stages. Artifact schemas MUST be stable, documented, and
versioned with backward-compatibility expectations defined per schema. Rationale: durable
artifacts are the system of record and enable replay, audit, and change management.

### III. Agentic Workflows for Semantic Tasks
Any task involving semantic reasoning or fuzzy equivalence MUST be implemented through an
agentic workflow and not static rules alone. Agent decisions, prompts, model metadata,
and outputs MUST be persisted as auditable artifacts. Rationale: semantic tasks require
adaptive reasoning and traceability for correctness review.
For this constitution, an "agentic workflow" minimally includes: explicit task framing,
model-mediated reasoning or tool use, persisted decision rationale, and deterministic
handoff of outputs to the next stage artifact.

### IV. CLI-First Execution
Every pipeline step MUST be invocable via CLI and expose `--input`, `--output`, and
`--config` flags, plus `--dry-run` where applicable. CLI contracts MUST be documented and
stable across compatible versions. Rationale: CLI-first interfaces ensure automation,
composition, and operational consistency.

### V. Extensibility Over Optimization
Design MUST favor explicit interfaces and composability over performance shortcuts. New
pipelines or stages MUST be addable without modifying existing stage behavior. Any
performance optimization that reduces modularity MUST include written justification and a
migration-safe extension path. Rationale: long-term adaptability outweighs local speedups.

### VI. Determinism & Reproducibility
Given identical inputs, artifacts, and configuration, pipeline outputs MUST be
reproducible. Any non-deterministic agent behavior MUST be explicitly logged with enough
metadata to explain variance, including model/version and randomness controls when used.
Rationale: reproducibility is required for debugging, trust, and governance.

## Operational Requirements

- Each stage interface MUST declare accepted artifact schema versions and produced schema
  versions.
- Each stage MUST validate input artifacts before processing and fail with explicit,
  machine-readable errors when validation fails.
- Machine-readable validation errors MUST be emitted as JSON with fields:
  `code`, `message`, `stage`, `artifact_path`, `schema_version`, and `details`.
- Validation `code` values MUST come from a documented, stable enum (for example:
  `SCHEMA_MISMATCH`, `MISSING_FIELD`, `TYPE_ERROR`, `CONSTRAINT_VIOLATION`).
- Each stage MUST emit an execution record artifact containing start time, end time,
  config hash, input artifact references, output artifact references, and status.
- Dry-run mode MUST never mutate artifacts and MUST report intended reads/writes.
- Artifact paths and schema versions MUST be configurable and not hard-coded.
- Artifacts containing prompts, model outputs, or decision logs MUST define retention
  policy (duration and deletion behavior), access policy (who can read), and redaction
  policy for sensitive data before release.

## Delivery Workflow & Compliance

- Plans MUST include a Constitution Check mapping feature scope to all six principles.
- Specs MUST define stage boundaries, artifact contracts, agentic decision points, and
  reproducibility requirements.
- Tasks MUST include implementation and verification work for CLI contracts, artifact
  persistence, idempotency checks, and non-determinism logging where applicable.
- Pull requests MUST include evidence of compliance; violations are architectural defects
  and block merge until resolved or formally waived.
- Waivers MUST be time-bound, documented with risk and rollback plan, and approved by
  maintainers before release.

## Governance

This constitution supersedes conflicting local conventions for pipeline architecture.
Amendments require: (1) a written proposal, (2) impact analysis across templates and
runtime guidance, and (3) maintainer approval. Compliance MUST be reviewed during planning,
specification, task generation, and pull request review.

Versioning policy follows semantic versioning for the constitution itself:
- MAJOR for backward-incompatible governance changes or principle removals/redefinitions.
- MINOR for new principles/sections or materially expanded obligations.
- PATCH for clarifications or non-semantic wording improvements.

Compliance expectations:
- Every feature plan MUST pass Constitution Check gates before implementation.
- Every release candidate MUST include evidence that stage CLIs, artifacts, and agent logs
  satisfy this constitution.
- Non-compliance discovered post-merge MUST trigger remediation tasks in the next sprint.

**Version**: 1.0.1 | **Ratified**: 2026-02-03 | **Last Amended**: 2026-02-03
