# Quickstart: Dataset Comparison Visualization Website

## Prerequisites

- Work from `/home/jacoberard/agent_practice/gdac/codex_work/data_analysis`
- Frontend dependencies installed in `site/`
- Comparable year data present in both scopes:
  - `outputs/analytics/<year>`
  - `outputs/analytics/<year>_full`

## Required Inputs For Each Selectable Year

1. Full hashtag + parent sources in `outputs/analytics/<year>_full`
   - `hashtag_frequency` artifact
   - `parent_company_groups` artifact
2. Celebrity frequency CSVs for both scopes
   - regular: `celebrity_freq.csv`
   - full: `celebrity_freq.csv`
3. Raw data sources for both scopes with columns:
   - `brand` (for raw brand clouds)
   - `text` (for tweet cards)
4. Full-scope tweet source includes `is_about_brand` when available.
   - If missing, logic treats missing as `false`.

## Run Locally

```bash
cd /home/jacoberard/agent_practice/gdac/codex_work/data_analysis/site
npm install
npm run dev
```

## Validate Required Behavior

1. Year dropdown:
   - Only years with both regular and full analytics folders are listed.
2. Word clouds:
   - Full combined hashtag+parent cloud.
   - Regular celebrity cloud.
   - Full celebrity cloud.
   - Regular raw brand cloud.
   - Full raw brand cloud.
3. Tweet cards:
   - One regular card and one full card.
   - Arrow navigation across total entries.
   - No duplicate `text` values per card.
   - Full card only uses `is_about_brand=false` rows (or missing treated as false).
4. Missing data states:
   - Missing files/columns display explicit non-blocking status.

## Suggested Verification Checks

- Seed duplicate tweet texts and verify dedupe output remains unique.
- Remove one required cloud input file and verify widget-level missing state without page crash.
- Switch across at least two years and confirm deterministic visualization updates.
