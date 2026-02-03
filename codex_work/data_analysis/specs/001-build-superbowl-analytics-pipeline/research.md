# Research: Twitter Super Bowl Analytics Pipeline

## 1) Runtime and CLI Framework

Decision: Use Python 3.11 with Typer for CLI entry points.

Rationale: Python offers strong CSV ecosystem support and Typer provides strict,
explicit argument contracts and clear help output.

Alternatives considered:
- Click: mature but less typed ergonomics for long-term CLI contracts.
- Rust clap: stronger performance but slower implementation iteration for this phase.

## 2) Tabular Processing Engine

Decision: Use pandas with chunked CSV ingestion and deterministic sort/write rules.

Rationale: pandas chunking (`chunksize`) directly satisfies memory constraints while
remaining approachable for analysts and maintainers.

Alternatives considered:
- Polars: excellent performance but requires broader team retooling.
- Dask: distributed value not required for initial architecture.

## 3) Schema Validation Strategy

Decision: Validate raw rows against a canonical schema using pydantic model contracts
and column-level validators during ingest.

Rationale: Pydantic yields explicit, testable validation errors and clear contracts for
upstream malformed data handling.

Alternatives considered:
- Ad hoc pandas checks: less reusable and weaker contract clarity.
- Great Expectations: powerful but heavier operational overhead for bootstrap stage.

## 4) Determinism and Artifact Lineage

Decision: Enforce deterministic ordering and stable serialization plus per-stage
manifest metadata.

Rationale: Deterministic ordering and explicit manifests provide reproducibility and
traceability across reruns and years.

Alternatives considered:
- Timestamp-only output naming: introduces non-deterministic artifacts.
- In-memory artifact passing: weakens restartability and lineage guarantees.

## 5) Sentiment and Text Mining Baseline

Decision: Start with VADER for sentiment and simple token/hashtag extraction,
then support module replacement behind analytics contracts.

Rationale: VADER is fast and appropriate for social text baseline sentiment while
preserving future module extensibility.

Alternatives considered:
- Transformer models: higher quality but heavier compute and serving complexity.
- Fully custom lexicon: slower delivery and maintenance burden.

## 6) Contract Surface Between CLI and Orchestrator

Decision: Define run requests and run manifests as versioned JSON structures and
publish REST-like OpenAPI contract for orchestration semantics.

Rationale: A formal contract clarifies responsibilities and enables future API/service
wrappers without redesign.

Alternatives considered:
- CLI-only undocumented coupling: faster initially but brittle and opaque.
- GraphQL schema: unnecessary for early pipeline control surfaces.
