# Quickstart: Data Visualization Website

## Local Development

1. Ensure the pipeline outputs exist under `outputs/analytics/<year>/`.
2. (Optional) Ensure aux outputs exist under `outputs/aux/<year>/`.
3. Start the site development server from `site/` (once scaffolded).

Example (placeholder):

```bash
cd site
npm install
npm run dev
```

## Required Artifacts (MVP)

- `outputs/analytics/<year>/hashtags_frequency.json`
- `outputs/analytics/<year>/mentions_frequency.json`

## Optional Artifacts (for advanced dashboards)

- `outputs/analytics/<year>/ad_sentiment_summary.json`
- `outputs/analytics/<year>/parent_company_sentiment_summary.json`
- `outputs/analytics/<year>/parent_company_sentiment_timeslices.json`
- `outputs/analytics/<year>/parent_company_deep_sentiment_summary.json`
- `outputs/analytics/<year>/parent_company_deep_sentiment_timeslices.json`
- `outputs/aux/<year>/parent_company_sentiment_breakdown.json`
- `outputs/aux/<year>/brand_sentiment_breakdown.json`
- `outputs/aux/<year>/parent_company_emotion_breakdown.json`
- `outputs/aux/<year>/brand_emotion_breakdown.json`

