<!--
Sync Impact Report
- Version change: 1.0.0 -> 1.0.1
- Modified principles:
  - Repository scope rule expanded to enforce in-directory work boundaries
- Added sections:
  - None
- Removed sections:
  - None
- Templates requiring updates:
  - ✅ no updates required (constitutional clarification only)
- Follow-up TODOs:
  - None.
-->
# Super Bowl Twitter Data Analysis Constitution

## Core Principles

### I. Year-Scoped Data Organization
All repository data MUST be organized by Super Bowl year using this structure:
`data/raw/<year>/`, `data/processed/<year>/`, `data/enriched/<year>/`, and
`data/analytics/<year>/`. Raw files in `data/raw` are immutable after ingest and MUST
never be modified by scripts. Every pipeline run MUST target a single explicit year or
single explicit data directory, and cross-year analysis is only permitted through an
explicit aggregation step.

Rationale: strict year isolation preserves lineage, prevents accidental overwrite, and
supports repeatable annual analysis.

### II. Modular, Stage-Based Pipeline Execution
The pipeline architecture MUST expose independent CLI-callable stages:
`ingest`, `clean`, `process`, `analyze`, `visualize` (optional), and `export`. Every
stage MUST accept explicit input paths and produce explicit output artifacts. The
system MUST support three execution modes: one stage for one year, full pipeline for
one year, and full pipeline for all available years.

Rationale: modular stages reduce coupling, improve debugging, and allow targeted reruns
without side effects.

### III. Deterministic and Scalable Processing
All processing and analytics steps MUST be deterministic for the same inputs and
configuration. Intermediate artifacts MUST be persisted to disk. Implementations MUST
use streaming or chunked processing where applicable and MUST NOT assume full datasets
fit in memory.

Rationale: reproducibility and scale are mandatory for large CSV-based social datasets.

### IV. Required Super Bowl Analytics Coverage
The analytics layer MUST, at minimum, support: brand/ad volume metrics, sentiment by
ad and brand over time, quarter/minute and before/after time analysis, ROI proxy
metrics (cost, followers, retweets, engagement proxies), relationship analysis among
key variables, event-aligned analysis (game events and ad timing), and text/network
analysis (hashtags, keywords, co-occurrence where applicable). Analytics outputs MUST
be written per year and MUST NOT overwrite other years.

Rationale: these capabilities define the repository's purpose and minimum analytical
completeness.

### V. Documentation and Extensibility by Default
A root `README.md` MUST exist and MUST be updated for every new feature, pipeline
stage, CLI command, or analytics capability. Documentation updates MUST state: what
changed, how to run it, required inputs, and produced outputs. Architecture MUST allow
adding new years with no code changes, adding analysis modules without breaking
existing ones, and future support for additional social platforms without restructuring
core directories.

Rationale: clear documentation and forward-compatible structure are required for long-
term maintainability and annual reuse.

## Repository Scope and Mandatory Data Layout
The repository purpose is to clean, process, and analyze large-scale Twitter CSV data
for Super Bowl analysis. Implementations MUST prioritize explicit configuration over
implicit behavior, reproducibility over speed, modularity over convenience, and
clarity over cleverness when requirements are ambiguous.
All work for this repository MUST remain within the `data_analysis` directory tree.
If additional structure is needed, new subdirectories MUST be created under
`data_analysis` rather than in parent or sibling directories.

Required layout:

```text
data/
  raw/
    <year>/
      *.csv
  processed/
    <year>/
  enriched/
    <year>/
  analytics/
    <year>/
```

## Delivery Workflow and Compliance Gates
All features MUST preserve independently runnable pipeline stages and explicit CLI
inputs (`--year` or `--data-dir`, and stage/all selection). Pull requests MUST include:
(1) deterministic execution confirmation, (2) proof that raw files remain unchanged,
(3) per-year output path verification, (4) memory-safety strategy for large files
(chunked/streaming where applicable), and (5) README updates for any new capability.

## Governance
This constitution supersedes conflicting local practices for this repository.
Amendments require a documented proposal, impact analysis across templates/docs, and
approval by repository maintainers. Versioning follows semantic rules: MAJOR for
backward-incompatible governance changes, MINOR for new principles or materially
expanded mandates, PATCH for clarifications with unchanged intent. Compliance reviews
MUST run during planning and pull request review using constitution-aligned checks in
`.specify/templates/plan-template.md`, `.specify/templates/spec-template.md`, and
`.specify/templates/tasks-template.md`.

**Version**: 1.0.1 | **Ratified**: 2026-02-03 | **Last Amended**: 2026-02-03
