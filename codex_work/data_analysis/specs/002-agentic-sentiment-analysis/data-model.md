# Data Model: Agentic Sentiment Analysis for X (Twitter) Data

## Entity: SentimentRunRequest

Fields:
- mode: enum(`year`, `data_dir`)
- year: string (YYYY, optional when `data_dir` used)
- data_dir: string (optional when `year` used)
- with_pipeline: boolean
- dry_run: boolean
- verbose: boolean
- deterministic: boolean

Validation:
- Exactly one of `year` or `data_dir` is required.
- `year` must match `^[0-9]{4}$` when present.

## Entity: AgentModelConfig

Fields:
- normalizer_model: string
- polarity_model: string
- emotion_model: string
- sarcasm_model: string
- supervisor_model: string
- request_delay_seconds: number
- max_rate_limit_retries: integer
- initial_backoff_seconds: number

Validation:
- All model fields must be non-empty.
- Retry/backoff values must be bounded and non-negative.

## Entity: NormalizerOutput

Fields:
- normalized_text: string
- removed_tokens: array[string]
- preserved_tokens: array[string]
- rationale: string

Validation:
- `normalized_text` required.
- Output must conform to strict JSON schema.

## Entity: PolarityOutput

Fields:
- sentiment: enum(`positive`, `neutral`, `negative`)
- confidence: number (0.0-1.0)
- rationale: string

Validation:
- `confidence` must be within [0.0, 1.0].

## Entity: EmotionOutput

Fields:
- emotion: enum(`joy`, `anger`, `disappointment`, `excitement`, `neutral`)
- confidence: number (0.0-1.0)
- rationale: string

Validation:
- One label only.

## Entity: SarcasmOutput

Fields:
- is_sarcastic: boolean
- confidence: number (0.0-1.0)
- rationale: string

Validation:
- Conservative bias defaults to `false` when uncertain.

## Entity: SupervisorOutput

Fields:
- sentiment: enum(`positive`, `neutral`, `negative`)
- confidence: number (0.0-1.0)
- flags: array[string]
- rationale: string

Validation:
- Must be emitted for every tweet.
- Flags may include `low_confidence`, `ambiguous`, `sarcasm_risk`.

## Entity: SentimentRecord

Fields:
- tweet_id: string
- year: integer
- final: object (`SupervisorOutput` subset: sentiment + confidence)
- agents: object
  - normalizer: `NormalizerOutput`
  - polarity: `PolarityOutput`
  - emotion: `EmotionOutput`
  - sarcasm: `SarcasmOutput`
- flags: array[string]

Validation:
- One output record per input tweet.
- Must be valid JSON object per line in JSONL output.

## Entity: SentimentSummaryArtifact

Fields:
- year: integer
- total_tweets: integer
- sentiment_counts: object
- emotion_counts: object
- sarcasm_rate: number
- low_confidence_count: integer
- generated_at_utc: datetime

Validation:
- Artifact path must remain under `outputs/analytics/<year>/`.
- Aggregates must match per-tweet record counts.

## Relationships

- SentimentRunRequest 1:1 AgentModelConfig
- SentimentRunRequest 1:N SentimentRecord
- SentimentRecord N:1 SentimentSummaryArtifact
