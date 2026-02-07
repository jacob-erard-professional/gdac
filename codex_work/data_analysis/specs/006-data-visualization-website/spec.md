# Specification: Data Visualization Website

## Objective

Create a read-only data visualization website that showcases the analyses
performed in this repository. The site must load year-scoped artifacts from
`outputs/analytics/<year>/` and `outputs/aux/<year>/` and present interactive,
auditable charts and tables for both sentiment and grouping outputs.

## Scope

### In Scope

- Static website under `site/` that can be run locally and deployed to static hosting.
- Year selector with per-year dashboards.
- Visualization of:
  - hashtag frequency
  - mention frequency
  - ad sentiment summaries
  - parent company sentiment summaries + time slices
  - parent company deep sentiment summaries + time slices
  - emotion breakdowns (brand + parent company)
- Download links for raw JSON/CSV/Parquet outputs.
- Clear empty-state handling when optional outputs are missing.
- Documentation for running the site locally.

### Out of Scope

- Modifying pipeline logic or upstream data contracts.
- Editing or mutating data outputs.
- Authentication, user accounts, or write-back features.
- Real-time inference or API services.

## Data Inputs

Minimum required:
- `outputs/analytics/<year>/hashtags_frequency.json`
- `outputs/analytics/<year>/mentions_frequency.json`

Optional (if present):
- `outputs/analytics/<year>/ad_sentiment_summary.json`
- `outputs/analytics/<year>/parent_company_sentiment_summary.json`
- `outputs/analytics/<year>/parent_company_sentiment_timeslices.json`
- `outputs/analytics/<year>/parent_company_deep_sentiment_summary.json`
- `outputs/analytics/<year>/parent_company_deep_sentiment_timeslices.json`
- `outputs/aux/<year>/parent_company_sentiment_breakdown.json`
- `outputs/aux/<year>/brand_sentiment_breakdown.json`
- `outputs/aux/<year>/parent_company_emotion_breakdown.json`
- `outputs/aux/<year>/brand_emotion_breakdown.json`

## UX Requirements

- Clear navigation between sections.
- Consistent chart styling and legends.
- Visible “data not available” states for missing artifacts.
- Ability to download the underlying file for each chart/table.

## Performance Requirements

- Load quickly on typical year datasets.
- Avoid rendering all charts at once; lazy-load per section where possible.

## Compatibility

- Works on modern Chrome/Firefox/Safari.
- Responsive layout for desktop and tablet.

## Success Criteria

- Visualizations match the underlying data outputs.
- Clear separation between analytics outputs and aux artifacts.
- Easy to navigate by year and analysis category.

