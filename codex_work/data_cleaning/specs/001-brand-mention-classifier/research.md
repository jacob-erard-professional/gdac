# Phase 0 Research

## Decision: Output format

**Decision**: Support CSV output by default (append `is_about_brand`,
`confidence`, `rationale`) and allow optional JSONL output via a CLI flag.

**Rationale**: CSV aligns with the input format and keeps the workflow simple;
JSONL is convenient for downstream pipelines without adding complexity.

**Alternatives considered**:
- Only CSV: simpler, but less flexible for integrations.
- Only JSONL: breaks parity with the input format.

## Decision: LLM interaction model

**Decision**: Use OpenRouter as the LLM provider with a provider-agnostic adapter
interface. The CLI supplies the OpenRouter API key via environment variable and
accepts a `--model` option to select the OpenRouter model.

**Rationale**: Keeps the prompt and CSV tooling independent of any specific
vendor and preserves testability.

**Alternatives considered**:
- Hard-code a single model without CLI selection: simpler, but limits flexibility.
- Direct vendor API usage: faster to start, but reduces portability.
- Prompt-only output without classification: fails the core requirement to
  decide about brand relevance.

## Decision: Prompt structure

**Decision**: Use a strict prompt that prioritizes `text`, allows other columns
as optional context, and requires a single JSON object response with
`is_about_brand`, `confidence`, and `rationale` fields.

**Rationale**: Deterministic parsing enables reliable batch processing and
unit tests.

**Alternatives considered**:
- Free-form answers: harder to parse and test.
- Multi-step prompts: more complex without clear benefit.

## Decision: Dependencies

**Decision**: Use Python standard library only for CSV, JSON, and CLI handling.

**Rationale**: Minimizes dependencies and aligns with simplicity and speed.

**Alternatives considered**:
- Pandas: convenient but heavier and unnecessary for basic CSV IO.
