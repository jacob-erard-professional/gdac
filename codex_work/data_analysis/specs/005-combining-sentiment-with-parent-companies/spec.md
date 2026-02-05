# Feature Specification: Combining Sentiment with Parent Companies

**Feature Branch**: `005-combining-sentiment-with-parent-companies`
**Date**: 2026-02-05
**Input**: User request to combine BERTweet sentiment with parent-company groupings to assess company image impact.

## Summary

Create a deterministic analytics step that joins BERTweet sentiment outputs with
parent-company groupings and enriched tweet metadata to produce per-parent
company sentiment impact summaries. Provide a standalone CLI command and optional
pipeline hook without changing default pipeline behavior.

## User Stories

### User Story 1 - Run parent-company sentiment impact for a year (P1)
As an analyst, I want to compute sentiment impact summaries for each parent
company for a given year so I can assess overall company image impact.

**Acceptance Criteria**
1. Given year-scoped sentiment output and parent-company groupings, when I run the
   command, then a summary JSON and CSV are written under `outputs/analytics/<year>/`.
2. If required inputs are missing, the command fails with a clear error.
3. Outputs are deterministic for the same inputs.

### User Story 2 - Optional pipeline integration (P2)
As a maintainer, I want to run parent-company sentiment impact as an optional
pipeline step so I can include it in automated runs without changing defaults.

**Acceptance Criteria**
1. `run --all --with-parent-company-sentiment` adds the new step; default runs are unchanged.
2. The step runs after sentiment and parent-company grouping artifacts exist.

## Functional Requirements

- **FR-001**: Join sentiment output (`sentiment/bertweet/<year>/sentiment.json`) with enriched rows
  (`data/enriched/<year>/enriched.csv`) on `tweet_id` + `year`.
- **FR-002**: Map enriched `brand_tag` or `ad_tag` to parent companies using
  `outputs/analytics/<year>/parent_company_groups.json`.
- **FR-003**: Produce per-parent metrics: tweet counts, sentiment counts, sentiment rates,
  net sentiment, average confidence, and confidence-weighted net sentiment.
- **FR-004**: Output a joined audit table in parquet and summary JSON/CSV under
  `outputs/analytics/<year>/`.
- **FR-005**: Provide a CLI command to run the step for a year or explicit data-dir.
- **FR-006**: Provide an optional pipeline hook via a flag.

## Non-Goals

- Model training or fine-tuning
- Any changes to upstream ingestion/cleaning
- Replacing existing sentiment or grouping workflows

## Inputs

- `sentiment/bertweet/<year>/sentiment.json`
- `outputs/analytics/<year>/parent_company_groups.json`
- `data/enriched/<year>/enriched.csv`

## Outputs

- `outputs/analytics/<year>/parent_company_sentiment_joined.parquet`
- `outputs/analytics/<year>/parent_company_sentiment_summary.json`
- `outputs/analytics/<year>/parent_company_sentiment_summary.csv`

## Validation & Testing

- Unit tests for join + aggregation logic.
- Integration test for pipeline flag behavior.
- Deterministic ordering checks.

