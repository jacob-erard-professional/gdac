# Data Model: Twitter Super Bowl Analytics Pipeline

## Entity: YearConfig

Fields:
- year: string (YYYY)
- raw_dir: string (absolute or repo-relative path)
- processed_dir: string
- enriched_dir: string
- analytics_dir: string
- run_mode: enum(`stage`, `full_year`, `full_all_years`)
- deterministic: boolean

Validation:
- Exactly one of `year` or `data_dir` may originate CLI resolution.
- `year` must match `^[0-9]{4}$`.

## Entity: StageContract

Fields:
- stage_name: enum(`ingest`, `clean`, `process`, `analyze`, `visualize`, `export`)
- input_paths: array[string]
- output_paths: array[string]
- params: object
- entrypoint: string

Validation:
- `input_paths` and `output_paths` must be explicit and non-empty.
- Output paths must not target `data/raw/`.

## Entity: RawTweetRecord

Fields:
- tweet_id: string (required)
- created_at: string/datetime (required)
- text: string (required)
- user_id: string (required)
- user_screen_name: string (optional)
- followers_count: integer (optional)
- retweet_count: integer (optional)
- favorite_count: integer (optional)
- brand_hint: string (optional)
- ad_hint: string (optional)

Validation:
- Required fields must exist in canonical schema.
- Missing optional fields are allowed and normalized downstream.

## Entity: ProcessedTweetRecord

Fields:
- selected RawTweetRecord fields preserved for lineage
- created_at_utc: datetime
- text_original: string
- cleaning_flags: string

Validation:
- Original `text` MUST be retained for lineage.
- `created_at_utc` is normalized when parseable; otherwise input is retained.

## Entity: EnrichedTweetRecord

Fields:
- all ProcessedTweetRecord fields
- hashtags: string (`|`-delimited)
- keywords: string (`|`-delimited)
- brand_tag: string
- ad_tag: string
- sentiment_score: number
- sentiment_label: enum(`negative`, `neutral`, `positive`)
- game_phase: string (`unknown` default when absent)

Validation:
- Feature extraction must be deterministic for identical inputs.

## Entity: AnalyticsArtifact

Fields:
- artifact_name: string
- year: string
- module: enum(`hashtags_frequency`, `mentions_frequency`, `custom`)
- file_path: string
- row_count: integer
- generated_at: datetime

Validation:
- Artifact path must remain under `outputs/analytics/<year>/`.

## Entity: RunManifest

Fields:
- run_id: string
- year: string
- stage: string
- input_files: array[string]
- output_files: array[string]
- record_counts: object
- started_at: datetime
- completed_at: datetime
- status: enum(`success`, `failed`)
- error_summary: string (optional)

Validation:
- Manifest required for every stage execution.
- `completed_at` must be >= `started_at`.

## Relationships

- YearConfig 1:N StageContract (a run resolves one config across multiple stages).
- StageContract 1:N RunManifest (each stage execution emits a manifest).
- RawTweetRecord -> ProcessedTweetRecord -> EnrichedTweetRecord lineage is preserved.
- EnrichedTweetRecord N:1 AnalyticsArtifact modules consume shared enriched data.
