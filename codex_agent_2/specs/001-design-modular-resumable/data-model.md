# Data Model - Modular, Resumable NLP Analytics Pipeline

## 1) StageDefinition
Represents a declarative stage contract used by the CLI and orchestrator.

Fields:
- `name` (string, required, unique): Stage identifier (for example `ingest`).
- `dependencies` (array[string], required): Explicit prerequisites.
- `input_schema_versions` (array[string], required): Accepted input schema versions.
- `output_schema_versions` (array[string], required): Produced output schema versions.
- `runner` (string, required): Import path/entrypoint for stage implementation.
- `supports_dry_run` (boolean, required).

Validation:
- `name` must match `^[a-z][a-z0-9_-]{1,63}$`.
- `dependencies` must reference existing `StageDefinition.name` values.
- Cycles are invalid.

Relationships:
- One `StageDefinition` can have many dependent `StageDefinition` entries.

## 2) ArtifactRecord
Immutable metadata for a concrete artifact generated or consumed by a stage.

Fields:
- `artifact_id` (string, required, unique).
- `artifact_type` (enum, required): `raw`, `cleaned`, `enriched`, `analysis`, `hashtag_candidates`, `hashtag_mappings`, `agent_trace`, `execution_record`.
- `schema_version` (string, required): SemVer-style string.
- `path` (string, required): Filesystem path.
- `checksum` (string, required): SHA-256 hash.
- `created_at` (datetime, required).
- `produced_by_stage` (string, required).
- `lineage` (object, optional): Parent artifact references.

Validation:
- `path` must be absolute or repo-relative normalized path.
- `checksum` must be lowercase hex length 64.

Relationships:
- Many `ArtifactRecord` items are referenced by one `StageRunRecord`.

## 3) StageRunRecord
Execution record artifact for one stage invocation.

Fields:
- `run_id` (string, required, unique).
- `stage_name` (string, required).
- `status` (enum, required): `started`, `succeeded`, `failed`, `skipped`.
- `start_time` (datetime, required).
- `end_time` (datetime, nullable until terminal).
- `config_hash` (string, required).
- `input_artifact_ids` (array[string], required).
- `output_artifact_ids` (array[string], required).
- `error` (object, optional): `{code,message,details}`.
- `determinism` (object, required):
  - `mode` (`deterministic` | `non_deterministic`)
  - `model_provider` (string, optional)
  - `model` (string, optional)
  - `model_version` (string, optional)
  - `temperature` (number, optional)
  - `seed` (integer, optional)

Validation:
- Terminal statuses (`succeeded`, `failed`, `skipped`) require `end_time`.
- `stage_name` must exist in `StageDefinition` registry.

Relationships:
- One `StageRunRecord` references many input/output `ArtifactRecord` entries.

## 4) PipelineManifest
Top-level execution/lineage registry for a pipeline workspace.

Fields:
- `manifest_version` (string, required).
- `pipeline_name` (string, required).
- `updated_at` (datetime, required).
- `stages` (array[StageDefinition], required).
- `runs` (array[StageRunRecord], required).
- `artifacts` (array[ArtifactRecord], required).

Validation:
- `manifest_version` must be supported by CLI runtime.
- `runs` and `artifacts` references must be internally consistent.

Relationships:
- Aggregates all stage definitions, runs, and artifact records.

## 5) HashtagCandidate
Observed hashtag evidence collected for normalization.

Fields:
- `candidate_id` (string, required, unique).
- `tag` (string, required): Raw hashtag token including `#`.
- `normalized_token` (string, required): Lowercased/preprocessed token.
- `frequency` (integer, required, >= 1).
- `contexts` (array[string], optional): Sample text references.

Validation:
- `tag` must start with `#` and length <= 100.

Relationships:
- Many candidates map to one `EquivalenceClass` through `HashtagMapping`.

## 6) EquivalenceClass
Canonical hashtag cluster discovered by the agent workflow.

Fields:
- `class_id` (string, required, unique).
- `canonical_tag` (string, required).
- `members` (array[string], required): Raw tags.
- `aggregate_confidence` (number, required, 0..1).
- `iteration` (integer, required, >= 1).

Validation:
- `canonical_tag` must appear in `members`.

Relationships:
- One class has many `HashtagMapping` entries.

## 7) HashtagMapping
Mapping from raw hashtag to canonical hashtag with provenance and lifecycle.

Fields:
- `mapping_id` (string, required, unique).
- `raw_tag` (string, required).
- `canonical_tag` (string, required).
- `confidence` (number, required, 0..1).
- `state` (enum, required): `draft`, `pending_review`, `approved`, `rejected`.
- `evidence` (array[string], optional): Decision rationale snippets/references.
- `agent_run_id` (string, required).
- `created_at` (datetime, required).

Validation:
- `confidence < review_threshold` defaults state to `pending_review` (future-ready rule).

Relationships:
- Belongs to one `StageRunRecord` (agent run) and one `EquivalenceClass`.

## State Transitions

### StageRunRecord.status
- `started -> succeeded`
- `started -> failed`
- `started -> skipped`
- Terminal states do not transition further.

### HashtagMapping.state
- `draft -> pending_review`
- `draft -> approved`
- `pending_review -> approved`
- `pending_review -> rejected`
- `rejected -> draft` (new iteration only; creates a new mapping record, does not mutate history)
