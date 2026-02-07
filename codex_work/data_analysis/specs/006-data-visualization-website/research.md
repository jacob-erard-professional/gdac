# Research: Data Visualization Website

## Goals

- Identify best-fit frontend framework and charting library for static deployment.
- Confirm which output artifacts are required vs optional.
- Determine best in-browser loading strategy for JSON/CSV/Parquet files.

## Artifact Inventory

Required (MVP):
- `outputs/analytics/<year>/hashtags_frequency.json`
- `outputs/analytics/<year>/mentions_frequency.json`

Optional:
- `outputs/analytics/<year>/ad_sentiment_summary.json`
- `outputs/analytics/<year>/parent_company_sentiment_summary.json`
- `outputs/analytics/<year>/parent_company_sentiment_timeslices.json`
- `outputs/analytics/<year>/parent_company_deep_sentiment_summary.json`
- `outputs/analytics/<year>/parent_company_deep_sentiment_timeslices.json`
- `outputs/aux/<year>/*` (maps, breakdowns, partials, recovered outputs)

## Framework Candidates

- Vite + React
- Vite + Svelte
- Vite + Vanilla (minimal)

## Charting Candidates

- ECharts (flexible, fast)
- Plotly (rich, heavier)
- Chart.js (simple)

## Loading Strategy

- JSON and CSV can be loaded directly via fetch.
- Parquet requires WASM or pre-converted JSON/CSV.
- Prefer JSON/CSV for browser rendering to keep dependencies light.

## Decisions Needed

- Final framework selection
- Charting library selection
- Whether to support Parquet directly or preconvert

