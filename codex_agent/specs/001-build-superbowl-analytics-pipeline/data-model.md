# Data Model: Super Bowl X Analytics Pipeline

## Entity: PipelineRun

- **Description**: One orchestrated execution for a specific event-year configuration.
- **Fields**:
  - `run_id` (string, required, unique)
  - `event_name` (string, required)
  - `year` (integer, required, 4-digit)
  - `config_hash` (string, required)
  - `status` (enum: pending, running, succeeded, failed, required)
  - `started_at` (datetime, required)
  - `ended_at` (datetime, optional)
  - `initiated_by` (string, optional)
  - `manifest_path` (string, required)
- **Validation Rules**:
  - `year` MUST be between 2000 and current year.
  - `ended_at` MUST be greater than or equal to `started_at` when present.

## Entity: RawSocialRecord

- **Description**: Unmodified social data point from X for Super Bowl context.
- **Fields**:
  - `source_record_id` (string, required)
  - `event_name` (string, required)
  - `year` (integer, required)
  - `captured_at` (datetime, required)
  - `author_id` (string, optional)
  - `text` (string, optional)
  - `engagement_counts` (object, optional)
  - `raw_payload` (object, required)
- **Validation Rules**:
  - `source_record_id` MUST be non-empty.
  - `raw_payload` MUST be preserved without mutation.

## Entity: CleanedSocialRecord

- **Description**: Quality-checked and normalized record derived from raw data.
- **Fields**:
  - `clean_record_id` (string, required, unique)
  - `source_record_id` (string, required)
  - `event_name` (string, required)
  - `year` (integer, required)
  - `normalized_text` (string, optional)
  - `language` (string, optional)
  - `is_valid` (boolean, required)
  - `rejection_reason` (string, optional)
  - `quality_flags` (array[string], optional)
- **Validation Rules**:
  - `source_record_id` MUST reference an existing `RawSocialRecord`.
  - `rejection_reason` MUST be present when `is_valid` is false.

## Entity: EnrichedSocialRecord

- **Description**: Cleaned record with derived attributes used by analytics.
- **Fields**:
  - `enriched_record_id` (string, required, unique)
  - `clean_record_id` (string, required)
  - `event_phase` (enum: pre_event, event_day, post_event, required)
  - `keyword_hits` (array[string], optional)
  - `sentiment_score` (number, optional)
  - `topic_label` (string, optional)
- **Validation Rules**:
  - `clean_record_id` MUST reference a valid `CleanedSocialRecord`.
  - `event_phase` MUST align with configured event windows.

## Entity: KPIDefinition

- **Description**: Canonical definition of a metric used for cross-year comparison.
- **Fields**:
  - `kpi_id` (string, required, unique)
  - `name` (string, required)
  - `definition_version` (string, required)
  - `formula_description` (string, required)
  - `unit` (string, required)
  - `aggregation_scope` (string, required)
- **Validation Rules**:
  - `definition_version` MUST follow semantic version format.
  - `formula_description` MUST be non-empty.

## Entity: YearlyKPIResult

- **Description**: Computed value of a KPI for a specific event-year run.
- **Fields**:
  - `run_id` (string, required)
  - `event_name` (string, required)
  - `year` (integer, required)
  - `kpi_id` (string, required)
  - `kpi_definition_version` (string, required)
  - `value` (number, required)
  - `confidence_note` (string, optional)
  - `quality_context` (object, required)
- **Validation Rules**:
  - (`run_id`, `kpi_id`) pair MUST be unique per run.
  - `kpi_definition_version` MUST match active definition at execution time.

## Entity: VisualizationAsset

- **Description**: Generated chart or infographic-ready artifact.
- **Fields**:
  - `asset_id` (string, required)
  - `run_id` (string, required)
  - `year` (integer, required)
  - `asset_type` (enum: chart, infographic_component, required)
  - `title` (string, required)
  - `source_kpis` (array[string], required)
  - `file_path` (string, required)
- **Validation Rules**:
  - `source_kpis` MUST reference existing `YearlyKPIResult` entries for `run_id`.

## Entity: AnalyticalSummary

- **Description**: Narrative output for white paper and executive communication.
- **Fields**:
  - `summary_id` (string, required)
  - `run_id` (string, required)
  - `audience_type` (enum: white_paper, executive, required)
  - `key_findings` (array[string], required)
  - `methodology_notes` (array[string], required)
  - `limitations` (array[string], required)
  - `file_path` (string, required)
- **Validation Rules**:
  - At least one methodology note and one limitation MUST be present.
  - Findings MUST be traceable to KPI IDs.

## Relationships

- `PipelineRun` 1:N `YearlyKPIResult`
- `PipelineRun` 1:N `VisualizationAsset`
- `PipelineRun` 1:N `AnalyticalSummary`
- `RawSocialRecord` 1:0..1 `CleanedSocialRecord`
- `CleanedSocialRecord` 1:0..1 `EnrichedSocialRecord`
- `KPIDefinition` 1:N `YearlyKPIResult`

## State Transitions

### PipelineRun.status

- `pending` -> `running` (orchestrator starts run)
- `running` -> `succeeded` (all stages complete and validations pass)
- `running` -> `failed` (stage failure or critical validation breach)

### Record Quality State

- Raw ingest -> Cleaned valid -> Enriched analyzed
- Raw ingest -> Cleaned invalid (with rejection reason) -> excluded from enrichment
