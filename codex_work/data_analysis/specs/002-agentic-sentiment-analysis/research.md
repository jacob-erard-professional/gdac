# Research: Agentic Sentiment Analysis for X (Twitter) Data

## 1) Multi-Agent Orchestration Pattern

Decision: Use LangChain runnables with parallel fan-out for independent agents
(polarity, emotion, sarcasm) after normalization, then supervisor fan-in.

Rationale: Matches committee-style design while keeping interfaces explicit and testable.

Alternatives considered:
- Sequential-only execution: simpler but slower and less aligned with architecture goals.
- Full graph orchestration framework: overkill for initial subsystem scope.

## 2) Structured Output Validation

Decision: Enforce strict JSON schema validation for each agent output and final record.

Rationale: Prevents malformed downstream artifacts and supports auditability.

Alternatives considered:
- Prompt-only formatting constraints: too brittle for production-like runs.
- Free-form rationale parsing: increases failure surface.

## 3) OpenRouter and Model Selection Strategy

Decision: Use OpenRouter-compatible model ids per agent with centralized config and
shared API key handling (`OPENROUTER_API_KEY`).

Rationale: Allows cost-aware model routing while preserving one integration path.

Alternatives considered:
- Single model for all agents: simpler but less cost-efficient.
- Provider-specific integration: less portable.

## 4) Reliability and Rate-Limit Handling

Decision: Include bounded retry/backoff and optional request delay controls.

Rationale: Reduces transient failure rate without unbounded runtime.

Alternatives considered:
- No retries: too fragile.
- Infinite retries: can stall runs and hide systemic failures.

## 5) Deterministic Artifact Strategy

Decision: Write per-tweet outputs as sorted JSONL records and aggregate summary JSON
with stable key ordering and deterministic naming.

Rationale: Supports rerun comparisons and constitutional repeatability requirements.

Alternatives considered:
- Timestamped filenames: breaks deterministic outputs.
- Single monolithic JSON array: less stream-friendly for large datasets.
