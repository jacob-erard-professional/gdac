# Implementation Plan: Modular, Resumable NLP Analytics Pipeline with Agentic Hashtag Normalization

**Branch**: `001-design-modular-resumable` | **Date**: 2026-02-03 | **Spec**: `/home/jacob/agent_practice/gdac_2/specs/001-design-modular-resumable/spec.md`
**Input**: Feature specification from `/home/jacob/agent_practice/gdac_2/specs/001-design-modular-resumable/spec.md`

## Summary

Design a new repository for a CLI-first NLP analytics pipeline with independently runnable stages (`ingest`, `clean`, `enrich`, `analyze`, `normalize-hashtags`), explicit artifact contracts, resumable execution, and an isolated agent loop for hashtag equivalence discovery with auditable outputs.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: Typer (CLI), Pydantic v2 (artifact schemas), NetworkX (dependency graph validation), PyYAML (config), Pandas (MVP data transforms)  
**Storage**: Versioned files on local filesystem (`artifacts/`) with JSON/YAML manifests  
**Testing**: pytest + contract tests for artifact schemas and CLI behavior  
**Target Platform**: Linux/macOS CLI environments
**Project Type**: single (library + CLI)  
**Performance Goals**: Execute non-agent stages on 100k rows in under 3 minutes on a dev laptop; skip-completed path starts in under 2 seconds  
**Constraints**: No implicit upstream execution; deterministic non-agent stages; agent stage logs model/version/seed/temperature and decision traces  
**Scale/Scope**: MVP supports one pipeline family with five stages and one agent loop; extension points for additional pipelines and review workflows

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Gate

- [x] Stage boundaries are explicit; each stage runs independently and is resumable.
- [x] No stage design implicitly triggers upstream stages.
- [x] Input/output artifacts are explicit, versioned, and schema-documented.
- [x] Semantic or fuzzy-equivalence logic is implemented via auditable agentic workflows.
- [x] Every stage defines CLI flags: `--input`, `--output`, `--config`, and `--dry-run` where applicable.
- [x] Design favors extension via new stages/pipelines without modifying existing ones.
- [x] Determinism plan is defined, including non-determinism logging for agent behavior.

### Post-Design Gate (after Phase 1)

- [x] Stage boundaries remain explicit with no hidden orchestration.
- [x] Manifest/data model includes versioned artifact lineage and stage run records.
- [x] Agent loop contract captures prompts, decisions, mappings, and confidence.
- [x] CLI and API contracts preserve separation between core pipeline and agent providers.
- [x] MVP vs Future scope is explicit in `quickstart.md` and architecture docs.

## Project Structure

### Documentation (this feature)

```text
specs/001-design-modular-resumable/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── pipeline-control.openapi.yaml
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── pipeline/
│   ├── stages/
│   │   ├── ingest.py
│   │   ├── clean.py
│   │   ├── enrich.py
│   │   ├── analyze.py
│   │   └── normalize_hashtags.py
│   ├── orchestrator.py
│   ├── dependencies.py
│   └── registry.py
├── artifacts/
│   ├── schemas/
│   ├── validator.py
│   └── manifest_store.py
├── agents/
│   ├── interfaces.py
│   ├── hashtag_normalizer.py
│   └── providers/
│       └── noop_provider.py
├── cli/
│   └── main.py
└── common/
    ├── config.py
    └── logging.py

tests/
├── unit/
├── integration/
└── contract/
```

**Structure Decision**: Use a single Python project with strict package boundaries so stage runtime, artifact contracts, and agent logic can evolve independently while preserving a unified CLI.

## Complexity Tracking

No constitutional violations or waivers required.
