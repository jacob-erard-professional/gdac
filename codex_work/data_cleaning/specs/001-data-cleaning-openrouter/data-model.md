# Data Model

## Entities

### TweetRecord
Represents a single raw tweet row plus all original columns.

**Fields**:
- `text`: string, required, non-empty
- `brand`: string, optional, may be empty or incorrect
- `*`: all other original columns preserved byte-for-byte

**Validation**:
- No columns are dropped or renamed.
- Any missing `text` or invalid type is quarantined and logged.

### ColumnRegistry
Defines the authoritative column list and types for the pipeline.

**Fields**:
- `columns`: array of `{ name, dtype, required, description }`
- `hash`: stable hash of the registry content
- `version`: semantic version for schema evolution

**Validation**:
- All input rows MUST match the registry.
- Additions/removals require explicit version bumps.

### NormalizedText
Deterministically normalized text used for agent inputs.

**Fields**:
- `text_normalized`: string
- `normalization_version`: string
- `source_text_hash`: string (hash of original `text`)

**Validation**:
- Unicode normalization applied deterministically.
- URL handling and whitespace normalization are stable and documented.

### BrandNormalization
Canonicalized brand label used for agent context.

**Fields**:
- `brand_original`: string
- `brand_normalized`: string
- `normalization_version`: string
- `alias_matched`: boolean

**Validation**:
- Original brand is preserved.
- Normalized values come only from config-driven alias tables.

### AgentInput
Explicit payload sent to the LLM agent.

**Fields**:
- `input_id`: string (stable hash of payload + prompt version + model params)
- `text_normalized`: string
- `brand_normalized`: string
- `brand_original`: string
- `metadata`: object (optional, explicitly included fields only)
- `prompt_version`: string
- `model`: string (primary model id)
- `router_model_params`: object (temperature, max_tokens, etc.)

**Validation**:
- Stateless: only explicit fields are allowed.
- No derived or hidden state.

### AgentOutput
Schema-validated response from the agent.

**Fields**:
- `input_id`: string (must match AgentInput)
- `brand_relevant`: boolean
- `confidence`: number (0.0-1.0)
- `rationale`: string (short justification)
- `router_model_used`: string
- `prompt_version`: string
- `output_hash`: string (hash of response payload)

**Validation**:
- Output is treated as suggestion only; does not overwrite `brand`.
- All fields required for auditability are present.

### Manifest
Per-step audit record.

**Fields**:
- `step_name`: string
- `run_id`: string
- `input_files`: array of `{ path, sha256 }`
- `output_files`: array of `{ path, sha256 }`
- `rows_in`: integer
- `rows_out`: integer
- `rows_rejected`: integer
- `rejection_reasons`: object (reason -> count)
- `created_at`: string (ISO 8601)

### AgentCacheEntry
Cached agent output keyed by deterministic hash.

**Fields**:
- `input_id`: string
- `request_hash`: string
- `response_hash`: string
- `response_payload`: object (AgentOutput)
- `cached_at`: string (ISO 8601)

### OpenRouterConfig
OpenRouter routing configuration.

**Fields**:
- `api_base`: string (default `https://openrouter.ai/api/v1`)
- `api_key_env`: string (env var name)
- `model`: string (primary model id)
- `models`: array of strings (optional fallback list)
- `model_params`: object
- `timeout_seconds`: integer
- `max_retries`: integer

## Relationships

- `TweetRecord` -> `NormalizedText` (1:1)
- `TweetRecord` -> `BrandNormalization` (1:1)
- `NormalizedText` + `BrandNormalization` -> `AgentInput` (1:1)
- `AgentInput` -> `AgentOutput` (1:1)
- Each step writes a `Manifest` referencing input/output files.
