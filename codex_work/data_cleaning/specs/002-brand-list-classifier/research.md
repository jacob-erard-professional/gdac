# Phase 0 Research

## Decision: Reuse-first implementation

**Decision**: Reuse existing `csv_io`, `openrouter_client`, and batch request
patterns from the brand-relevance workflow, with a dedicated brand-list logic
module for category assignment.

**Rationale**: Minimizes rework, limits regression risk, and follows simplicity
constraints.

**Alternatives considered**:
- Rebuild an independent classifier stack: rejected due to duplication.
- Fold all logic into existing modules only: rejected due to reduced clarity.

## Decision: Row filtering and output retention

**Decision**: Keep all input rows in output, but classify only rows where
`is_about_brand` is false-like; true rows are marked as skipped with fixed
output fields.

**Rationale**: Matches clarified requirements, prevents row loss, and preserves
auditable output.

**Alternatives considered**:
- Drop true rows from output: rejected due to row reconciliation loss.
- Omit classification fields for skipped rows: rejected due to inconsistent
  schema.

## Decision: Brand list ingestion

**Decision**: Accept a one-column CSV with required header `brand` as the
candidate brand source.

**Rationale**: Explicit format reduces parsing ambiguity and improves
repeatability.

**Alternatives considered**:
- Comma-separated CLI list only: rejected by clarified requirement.
- Headerless CSV: rejected due to weaker validation.

## Decision: Category and suggestion policy

**Decision**: Enforce `listed_brand | new_brand | no_brand` for candidate rows,
plus `skipped` for pre-filtered rows; for `new_brand`, preserve
`suggested_brand` without auto-promotion.

**Rationale**: Provides deterministic, testable outputs with reviewable
suggestions.

**Alternatives considered**:
- Auto-promote `suggested_brand`: rejected due to taxonomy-control risk.
- Collapse `new_brand` into `no_brand`: rejected due to information loss.
