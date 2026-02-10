<!--
Sync Impact Report
- Version change: 1.0.0 -> 1.1.0
- Modified principles: I-V renumbered after new documentation principle
- Added sections: None
- Removed sections: None
- Templates requiring updates:
  - .specify/templates/plan-template.md [updated]
  - .specify/templates/spec-template.md [updated]
  - .specify/templates/tasks-template.md [updated]
  - .specify/templates/commands/*.md [not found in repo]
- Follow-up TODOs: None
-->
# data_cleaning Constitution

## Core Principles

### I. Documentation Above All
Documentation is valued above everything else. The `README.md` MUST be updated
to describe all existing functionality and how to run it whenever changes are
made. Documentation for new or changed behavior MUST be completed before the
behavior is considered done. Rationale: shared understanding and reproducible
use outweigh all other priorities.

### II. Simplicity First
Build the simplest viable solution and prefer clear, small components over
abstraction. New complexity MUST be justified with a concrete need and a
rejected simpler alternative. Rationale: simplicity preserves speed of delivery
and testability.

### III. Testability Is Non-Negotiable
All production code MUST be covered by automated tests. Each user story MUST
have at least one independent test, and core logic MUST have unit tests.
Tests MUST be deterministic and run in CI using `pytest` unless a different
runner is required for a non-Python component. Rationale: testability enables
safe iteration and refactoring.

### IV. Python-First by Default
Python is the default language and tooling for this repository. Non-Python code
is allowed only when a documented performance target cannot be met in Python and
profiling evidence supports the exception. Rationale: a single primary language
maximizes simplicity and testability.

### V. Performance With Evidence
Performance work MUST be driven by measurements. Any optimization or language
exception requires benchmarks or profiling results, plus a stated target and a
verification step. Rationale: speed matters, but only where it is proven to be a
bottleneck.

### VI. Repository-Local Artifacts
All files and generated outputs MUST remain within the `data_cleaning`
repository. Temporary files may be placed in `/tmp`, but no workflow may depend
on writing outside the repository for permanent artifacts. Rationale: ensures
reproducibility and auditable changes.

## Technical Constraints

- The primary implementation language is Python; the specific version MUST be
  declared in `specs/[###-feature-name]/plan.md`.
- Non-Python components require a performance justification and a benchmark.
- All tooling, scripts, and outputs MUST operate within the repository root
  (except temporary files in `/tmp`).

## Development Workflow

- Every feature MUST have a spec, plan, and tasks list aligned to this
  constitution before implementation starts.
- A Constitution Check MUST be completed during planning and re-checked after
  design updates.
- Tests MUST be written and failing before implementation of the associated
  behavior.
- Documentation updates, including `README.md`, MUST be completed before
  features are considered done.
- Performance targets and benchmarks are REQUIRED for any non-Python component
  or performance-critical path.
- Code review MUST verify compliance with simplicity, testability, and
  documentation, and performance evidence requirements.

## Governance

Amendments require a written proposal, rationale, and approval by repository
maintainers. Versioning follows semantic rules: MAJOR for principle removals or
redefinitions, MINOR for new principles or material expansions, PATCH for
clarifications. Compliance reviews are required for every spec/plan/tasks set
and for each PR touching production code. The constitution supersedes any
conflicting guidance elsewhere in the repository.

**Version**: 1.1.0 | **Ratified**: 2026-02-10 | **Last Amended**: 2026-02-10
