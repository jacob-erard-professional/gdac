# Phase 0 Research: Deterministic Twitter (X) Data Cleaning + OpenRouter Agents

## Decisions

### OpenRouter API integration

**Decision**: Use OpenRouter's OpenAI-compatible chat completions endpoint at
`https://openrouter.ai/api/v1/chat/completions` with Bearer token authentication.

**Rationale**: OpenRouter documents Bearer token auth and OpenAI-compatible request/response
schemas, enabling deterministic, stateless agent calls without custom model adapters.
Optional headers (`HTTP-Referer`, `X-Title`) can identify the application without affecting
functionality.

**Alternatives considered**:
- Use provider-specific SDKs directly (rejected: violates routing/cost-control boundary).
- Use non-chat endpoints (rejected: chat schema is documented as the normalized interface).

### Model selection and routing

**Decision**: Models are configured in config files as a primary model ID with an optional
fallback list via the `models` parameter. Default behavior uses explicit `model` if set.

**Rationale**: OpenRouter supports `model` and `models` routing to provide fallback behavior
when providers are unavailable or rate-limited; configuration keeps this swappable without
code changes.

**Alternatives considered**:
- Always use `openrouter/auto` (rejected: reduces reproducibility and makes model identity
  harder to control).
- Hardcode a specific model (rejected: violates configurability requirement).

### Request/response logging for reproducibility

**Decision**: Log the request payload, model name, parameters, prompt version, and input
hash for every agent call. Capture the `model` field returned in OpenRouter responses.

**Rationale**: OpenRouter normalizes the response schema and includes the `model` used; this
supports reproducible auditing of which model actually served the request.

**Alternatives considered**:
- Only log input hash and output (rejected: insufficient for auditing model routing).

### Language and libraries

**Decision**: Implement in Python 3.11 with `pandas` for CSV handling, `pydantic` for schema
validation, `pyyaml` for config, `httpx` for OpenRouter HTTP calls, `tenacity` for retries,
and `orjson` for deterministic JSON serialization.

**Rationale**: The stack is well-suited for deterministic data processing, schema validation,
and explicit HTTP client control. All behavior will be config-driven.

**Alternatives considered**:
- Node.js + TypeScript (rejected: existing repo defaults are unknown; Python is common for
  data cleaning and allows strict schema handling via `pydantic`).

### Caching strategy for agent outputs

**Decision**: Cache agent outputs keyed by a stable hash of: prompt version, agent input
payload, model ID, and model parameters. Cache entries are stored as JSON in
`data/intermediate/agent_cache/` and replayed deterministically.

**Rationale**: Hash-based caching ensures agent outputs are reproducible and re-playable
without re-calling OpenRouter.

**Alternatives considered**:
- No caching (rejected: violates reproducibility requirement for agent outputs).

## Sources Consulted

- OpenRouter API authentication documentation
- OpenRouter API reference (OpenAPI schema, request/response shapes)
- OpenRouter model routing documentation
