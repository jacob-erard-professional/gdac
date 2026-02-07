# Data Model: Data Visualization Website

## Overview

The visualization site consumes year-scoped artifacts from `outputs/analytics/<year>/`
and `outputs/aux/<year>/`. The data model is client-side and read-only.

## Core Entities

### Year
- `year`: string (e.g., "2024")
- `analytics_dir`: `outputs/analytics/<year>/`
- `aux_dir`: `outputs/aux/<year>/`

### HashtagFrequency
- `year`
- `hashtags`: list of `{hashtag, count}`

### MentionFrequency
- `year`
- `mentions`: list of `{mention, count}`

### AdSentimentSummary
- `ads`: list of `{ad_tag, tweet_count, positive_rate, neutral_rate, negative_rate, net_sentiment, avg_confidence, weighted_net_sentiment}`

### ParentCompanySentimentSummary
- `parents`: list of `{parent_company, tweet_count, positive_rate, neutral_rate, negative_rate, net_sentiment, avg_confidence, weighted_net_sentiment, weighted_lift_vs_overall}`

### ParentCompanySentimentTimeslices
- `time_slices`: list of `{parent_company, time_slice_start, tweet_count, positive_rate, neutral_rate, negative_rate, net_sentiment}`

### ParentCompanyDeepSentimentSummary
- `parents`: list of `{parent_company, tweet_count, avg_confidence, <emotion>_count, <emotion>_rate}`

### ParentCompanyDeepSentimentTimeslices
- `time_slices`: list of `{parent_company, time_slice_start, tweet_count, avg_confidence, <emotion>_count, <emotion>_rate}`

### EmotionBreakdown
- list of `{parent_company|brand, sentiment_breakdown, tweet_count}`

## Optional Artifacts

- `outputs/aux/<year>/sentiment_company_map.jsonl`
- `outputs/aux/<year>/deep_sentiment_company_map.jsonl`
- `outputs/aux/<year>/parent_company_tweet_map.jsonl`

## Empty States

If optional artifacts are missing, UI should:
- show a placeholder with “data not available”
- provide guidance on which command generates the file

