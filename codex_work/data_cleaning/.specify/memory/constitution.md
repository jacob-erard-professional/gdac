<!--
Sync Impact Report
- Version change: 1.0.0 -> 1.1.0
- Modified principles: None
- Added sections: None
- Removed sections: None
- Templates requiring updates: ✅ updated .specify/templates/tasks-template.md
- Follow-up TODOs: TODO(RATIFICATION_DATE): original adoption date not found in repository; TODO(README_RUN_INSTRUCTIONS): add concrete CLI commands once implemented
-->
# Twitter (X) Data Cleaning Constitution

## Core Principles

### Determinism Over Cleverness
- Given the same input data and configuration, the pipeline MUST always produce the same outputs.
- No non-deterministic operations are allowed unless explicitly seeded and documented.
- Any step that depends on ordering MUST make the ordering explicit and stable.
Rationale: Determinism is required for auditability and reproducibility in downstream analysis.

### Modular Step-Based Pipeline
- Each data cleaning concern MUST live in its own clearly defined step.
- Steps MUST be runnable independently and composable into a full pipeline.
- Each step MUST read from exactly one input directory and write to exactly one output directory.
- Each step MUST produce a manifest with input hashes, output hashes, row counts before/after,
  and rejection counts with reasons.
Rationale: Modular, composable steps keep the pipeline explainable and testable.

### Schema-First Validation
- All datasets MUST adhere to explicit schemas including `text` (string, non-empty) and
  `brand` (string, may be empty or incorrect).
- The pipeline MUST NOT perform silent column dropping, silent type coercion, or implicit
  renaming.
- Rows that violate schema requirements MUST be logged, counted, and either corrected
  explicitly or quarantined.
Rationale: Schema enforcement prevents hidden data loss and preserves trust in outputs.

### Brand Skepticism & Preservation
- The `brand` column is treated as a hypothesis, not truth.
- Brand validation, correction, or rejection MUST be explicit and traceable.
- Brand relevance checks MUST produce explicit flags or confidence scores and MUST NOT
  overwrite the original `brand` value.
Rationale: Brand labels are noisy and require explicit, auditable handling.

### Raw Data Immutability & Explainability
- Raw input data MUST NEVER be mutated or overwritten.
- All derived data MUST be written to new, versionable artifacts.
- Every transformation MUST be explainable by reading the code and README; no "magic" steps.
- All thresholds, heuristics, and toggles MUST live in configuration files with defaults
  documented.
Rationale: Immutability and explainability keep the pipeline safe, reviewable, and
maintainable.

## Pipeline & Data Standards

- Repository layout MUST follow: `data/raw`, `data/intermediate`, `data/clean`, `src/ingest`,
  `src/cleaning`, `src/brand`, `src/text`, `src/orchestrator`, `src/config`, and `scripts`.
- `data/raw` is for original input CSVs and is read-only.
- `data/intermediate` is for step outputs; `data/clean` is for final datasets.
- Cleaning categories MUST exist as separate steps: Schema Validation; Text Normalization
  (Unicode, URL handling, whitespace, optional casing); Noise Handling (retweets, duplicates,
  rule-based bot or empty content); Brand Normalization (canonical labels, alias handling,
  case normalization); Brand Relevance Validation (flags or confidence scores, no overwrite).
- Logs MUST be structured and machine-readable, capturing rows in/out and rejections.
- Failures MUST be loud and actionable.

## Documentation & Change Control

- The repository MUST expose a CLI that supports running a single step, the full pipeline,
  selecting input/output directories, and dry-run or validation-only mode.
- The CLI MUST NOT contain business logic; logic lives in `src/` modules.
- The README MUST explain the repository purpose, each pipeline step, how to run the
  pipeline, and all configuration options.
- Any new feature or cleaning step MUST update the README, including how to run that
  feature.
- The repository MUST NOT: train machine learning models; perform sentiment or emotion
  analysis; perform aggregation or reporting; or make irreversible assumptions about brand
  correctness.

## Governance

- This constitution supersedes all other practices in this repository.
- Amendments require updating this file, reflecting changes in templates and runtime
  guidance docs, and documenting any migrations or behavior changes.
- Versioning follows semantic versioning: MAJOR for backward-incompatible governance changes
  or removals; MINOR for new principles or materially expanded guidance; PATCH for
  clarifications or wording improvements.
- Compliance review is mandatory for all changes; pull requests that modify behavior
  without corresponding documentation updates are invalid.

**Version**: 1.1.0 | **Ratified**: TODO(RATIFICATION_DATE): original adoption date not found in repository | **Last Amended**: 2026-02-09
