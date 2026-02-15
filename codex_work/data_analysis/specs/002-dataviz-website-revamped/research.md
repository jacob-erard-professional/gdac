# Phase 0 Research: Dataset Comparison Visualization Website

## Decision: Year dropdown eligibility

- **Decision**: Include only years where both `outputs/analytics/<year>` and `outputs/analytics/<year>_full` exist.
- **Rationale**: Clarified requirement is strict side-by-side comparison; single-sided years should not appear as selectable.
- **Alternatives considered**:
  - Include either-side years with partial state: rejected because it conflicts with clarified dropdown rule.
  - Include all years and disable unsupported ones: rejected as unnecessary complexity for current scope.

## Decision: Full dataset path convention

- **Decision**: Resolve full dataset analytics from `outputs/analytics/<year>_full`.
- **Rationale**: This path was explicitly selected in clarification and keeps deterministic mapping from selected year.
- **Alternatives considered**:
  - Shared non-year `year_full` directory: rejected as non-scalable.
  - Multi-pattern auto-detection: rejected to avoid ambiguity.

## Decision: Full hashtag+parent word cloud composition

- **Decision**: Create one full-dataset cloud by combining normalized term counts from full `hashtag_frequency` and full `parent_company_groups`.
- **Rationale**: Requirement asks for one cloud sourced from both artifacts.
- **Alternatives considered**:
  - Two separate clouds: rejected (does not meet single-cloud requirement).
  - Hashtag-only cloud: rejected (drops parent-company signal).

## Decision: Celebrity and brand clouds per scope

- **Decision**: Render distinct regular/full clouds for `celebrity_freq.csv` and raw `brand` frequency.
- **Rationale**: Required comparison depends on scope-separated views.
- **Alternatives considered**:
  - Merged cloud: rejected because scope contrast is lost.

## Decision: Tweet card scope and filtering

- **Decision**: Show tweet cards for both regular and full datasets; for full, include rows where `is_about_brand=false`, and when field is missing treat as `false`.
- **Rationale**: Matches clarified scope and filter fallback.
- **Alternatives considered**:
  - Full-only card: rejected (clarified against).
  - Mark full card unavailable when field missing: rejected by clarification.

## Decision: Duplicate tweet text handling

- **Decision**: Deduplicate per card using normalized text key (`trim -> collapse whitespace -> lowercase`), keeping first-seen order.
- **Rationale**: Prevents duplicates while preserving deterministic, stable navigation order.
- **Alternatives considered**:
  - Exact text match only: rejected due to case/whitespace duplicates.
  - Fuzzy dedupe: rejected due to non-deterministic behavior risk.

## Decision: Missing data behavior

- **Decision**: Keep page functional and show explicit non-blocking missing states at widget level for absent files/columns.
- **Rationale**: Allows users to use available visuals without losing transparency.
- **Alternatives considered**:
  - Hard fail whole page: rejected for poor usability.
