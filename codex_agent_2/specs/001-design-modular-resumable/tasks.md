# Tasks: Modular, Resumable NLP Analytics Pipeline with Agentic Hashtag Normalization

**Input**: Design documents from `/home/jacob/agent_practice/gdac_2/specs/001-design-modular-resumable/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required), `research.md`, `data-model.md`, `contracts/pipeline-control.openapi.yaml`, `quickstart.md`

**Tests**: Validation tasks are explicitly required and included for schema checks, determinism logging, and idempotent reruns.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and baseline tooling.

- [X] T001 Create repository scaffolding in `src/`, `tests/`, `configs/`, and `artifacts/` directories (`src/pipeline/stages/`, `src/artifacts/schemas/`, `src/agents/providers/`, `src/cli/`, `tests/unit/`, `tests/integration/`, `tests/contract/`)
  - Inputs: `plan.md` project structure section.
  - Outputs: Directory tree and placeholder `__init__.py` files.
  - Definition of Done: All planned directories/files exist and `python -m pytest --collect-only` runs without import-path errors.
  - Scope: MVP.

- [X] T002 Initialize Python package and dependencies in `pyproject.toml` (Typer, Pydantic v2, PyYAML, NetworkX, Pandas, pytest)
  - Inputs: `plan.md` technical context.
  - Outputs: `pyproject.toml`, lock file (if used), installable project metadata.
  - Definition of Done: `python -m pip install -e .` succeeds and `pipeline --help` entrypoint is discoverable.
  - Scope: MVP.

- [X] T003 [P] Add baseline developer tooling in `pytest.ini` and `.gitignore`
  - Inputs: Existing repo config and artifact path conventions.
  - Outputs: Test discovery config and ignore rules for runtime artifacts/logs.
  - Definition of Done: `pytest --collect-only` and `git status` show expected behavior (no accidental artifact tracking).
  - Scope: MVP.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core contracts and interfaces required by all user stories.

- [X] T004 Define stage dependency registry model in `src/pipeline/dependencies.py`
  - Inputs: `data-model.md` (`StageDefinition`) and `spec.md` FR-006.
  - Outputs: `StageDefinition` model and static registry for `ingest`, `clean`, `enrich`, `analyze`, `normalize-hashtags`.
  - Definition of Done: Registry validates known stages and rejects unknown stage/dependency references.
  - Scope: MVP.

- [X] T005 [P] Define artifact/manifest schemas in `src/artifacts/schemas/manifest.py`
  - Inputs: `data-model.md` (`ArtifactRecord`, `StageRunRecord`, `PipelineManifest`), constitution requirements.
  - Outputs: Pydantic models with schema version fields and validation constraints.
  - Definition of Done: Schema models serialize/deserialize sample manifest and enforce required fields.
  - Scope: MVP.

- [X] T006 Implement manifest store and append-only run recording in `src/artifacts/manifest_store.py`
  - Inputs: T005 schema models and filesystem layout from `quickstart.md`.
  - Outputs: Read/write API for manifest plus run/artifact append helpers.
  - Definition of Done: Writes valid `artifacts/manifest.json` and preserves immutable historical runs.
  - Scope: MVP.

- [X] T007 [P] Implement artifact schema validator and machine-readable errors in `src/artifacts/validator.py`
  - Inputs: T005 schemas and constitution validation error contract.
  - Outputs: Validation helpers returning `{code,message,stage,artifact_path,schema_version,details}`.
  - Definition of Done: Invalid artifacts emit required error payload with stable enum codes.
  - Scope: MVP.

- [X] T008 Define agent interface boundary in `src/agents/interfaces.py` and no-op provider in `src/agents/providers/noop_provider.py`
  - Inputs: `research.md` Decision 5 and `spec.md` FR-007.
  - Outputs: `HashtagNormalizerAgent` protocol/interface and provider abstraction.
  - Definition of Done: Core pipeline imports only interface, not vendor SDKs.
  - Scope: MVP.

- [X] T009 Implement base CLI app and command groups in `src/cli/main.py`
  - Inputs: `quickstart.md` CLI examples and FR-001/FR-002.
  - Outputs: Typer CLI groups (`stage run`, `stage run-many`, `artifacts manifest show`) with required options.
  - Definition of Done: CLI help includes mandatory flags (`--input`, `--output`, `--config`, `--dry-run`).
  - Scope: MVP.

---

## Phase 3: User Story 1 - Run Isolated Stages with Artifact Reuse (Priority: P1) 🎯 MVP

**Goal**: Execute individual or selected stages independently with explicit dependencies and skip logic.

**Independent Test**: Run `ingest` once, then run `clean,analyze` subset with `--skip-completed`; verify no implicit upstream execution.

- [X] T010 [US1] Implement stage runner contract in `src/pipeline/orchestrator.py`
  - Inputs: T004 dependency registry and T009 CLI command inputs.
  - Outputs: `run_stage(stage_name, input_paths, output_paths, config, dry_run)` orchestration method.
  - Definition of Done: Invoking one stage does not execute undeclared/unselected stages.
  - Scope: MVP.

- [X] T011 [P] [US1] Implement concrete stage modules in `src/pipeline/stages/ingest.py`, `src/pipeline/stages/clean.py`, `src/pipeline/stages/enrich.py`, and `src/pipeline/stages/analyze.py`
  - Inputs: Stage contracts from T010 and quickstart flow.
  - Outputs: Deterministic stage handlers with explicit input/output handling.
  - Definition of Done: Each stage runs independently with valid artifacts and dry-run support.
  - Scope: MVP.

- [X] T012 [US1] Implement dependency validation for selected stage sets in `src/pipeline/dependencies.py`
  - Inputs: T004 registry and FR-006.
  - Outputs: Validation function that blocks execution when required dependencies are missing from selected subset.
  - Definition of Done: Subset command fails fast with `DEPENDENCY_ERROR` and does not auto-run missing dependencies.
  - Scope: MVP.

- [X] T013 [US1] Implement skip-completed artifact reuse logic in `src/pipeline/orchestrator.py`
  - Inputs: T006 manifest store and T007 validator.
  - Outputs: `should_skip_stage` logic based on manifest terminal status + output artifact/schema checks.
  - Definition of Done: Completed stages are skipped only when outputs and schema versions both match.
  - Scope: MVP.

- [X] T014 [US1] Wire CLI execution paths to orchestrator in `src/cli/main.py`
  - Inputs: T010–T013.
  - Outputs: Working `stage run` and `stage run-many` command handlers.
  - Definition of Done: Commands execute in declared order for selected stages only and write run records.
  - Scope: MVP.

- [X] T015 [US1] Validate rerunning individual stages without side effects in `tests/integration/test_stage_rerun_idempotency.py`
  - Inputs: T010–T014 and sample config/data fixtures.
  - Outputs: Integration test asserting deterministic outputs/checksums and no implicit upstream runs.
  - Definition of Done: Test fails before implementation and passes after; repeated runs preserve correctness.
  - Scope: MVP.

---

## Phase 4: User Story 2 - Track Artifact Lineage via Registry/Manifest (Priority: P2)

**Goal**: Persist and inspect complete stage/artifact lineage with schema validation.

**Independent Test**: Execute two stages and verify manifest includes required lineage fields and valid schema versions.

- [X] T016 [US2] Implement artifact registration hooks in `src/pipeline/registry.py`
  - Inputs: T005/T006 models/store and stage outputs from US1.
  - Outputs: Helpers that register input/output artifacts and link them to run records.
  - Definition of Done: Every successful stage invocation appends corresponding artifact records.
  - Scope: MVP.

- [X] T017 [US2] Integrate manifest recording into orchestrator in `src/pipeline/orchestrator.py`
  - Inputs: T016 and US1 orchestration.
  - Outputs: Automatic start/success/failure/skipped run state updates plus config hash persistence.
  - Definition of Done: Manifest captures `stage name`, `input artifacts`, `output artifacts`, `schema version`, `status`, and timestamps per run.
  - Scope: MVP.

- [X] T018 [US2] Expose manifest inspection command in `src/cli/main.py`
  - Inputs: T006 store API and quickstart command requirements.
  - Outputs: `pipeline artifacts manifest show --path ...` output renderer.
  - Definition of Done: Operators can inspect manifest lineage from CLI without editing files manually.
  - Scope: MVP.

- [X] T019 [US2] Validate artifact schema contracts in `tests/contract/test_manifest_schema_contract.py`
  - Inputs: T005 schemas, T007 validator, and sample manifest fixtures.
  - Outputs: Contract test for required fields, schema versions, and validation errors.
  - Definition of Done: Invalid manifests produce required error shape and valid manifests pass.
  - Scope: MVP.

---

## Phase 5: User Story 3 - Normalize Hashtags with Agentic Equivalence Discovery (Priority: P3)

**Goal**: Run an isolated agent loop that discovers hashtag equivalences and feeds normalized data into analysis.

**Independent Test**: Run `normalize-hashtags` on candidate hashtags and verify mappings, confidence, and trace artifacts are persisted and reusable.

- [X] T020 [US3] Design hashtag equivalence schemas in `src/artifacts/schemas/hashtag_normalization.py`
  - Inputs: `data-model.md` (`HashtagCandidate`, `EquivalenceClass`, `HashtagMapping`).
  - Outputs: Pydantic models for candidates, classes, mappings, trace metadata, and iteration versioning.
  - Definition of Done: Schema validates confidence range, lifecycle state enum, and iteration requirements.
  - Scope: MVP.

- [X] T021 [US3] Implement hashtag normalization agent loop in `src/agents/hashtag_normalizer.py`
  - Inputs: T008 interface boundary and T020 schemas.
  - Outputs: Iterative normalization workflow returning equivalence classes, mappings, and decision evidence.
  - Definition of Done: One full loop runs with provider abstraction and yields confidence-scored mappings.
  - Scope: MVP.

- [X] T022 [US3] Persist and reload agent outputs in `src/pipeline/stages/normalize_hashtags.py` and `src/artifacts/manifest_store.py`
  - Inputs: T021 outputs and T006 store APIs.
  - Outputs: Versioned mapping artifacts and trace artifacts that can be reused as explicit inputs for next iteration.
  - Definition of Done: Iteration N+1 can consume N outputs without mutating prior artifacts.
  - Scope: MVP.

- [X] T023 [US3] Integrate normalized hashtags into downstream analysis in `src/pipeline/stages/analyze.py`
  - Inputs: Normalized mapping artifacts from T022 and analysis stage contract from US1.
  - Outputs: Analysis stage consumes canonical hashtags when provided.
  - Definition of Done: Analysis output reflects canonical tags and remains runnable independently.
  - Scope: MVP.

- [X] T024 [US3] Validate agent determinism metadata logging in `tests/integration/test_agent_determinism_logging.py`
  - Inputs: Agent stage runs from T021/T022 and manifest schema from US2.
  - Outputs: Integration test ensuring run records include provider/model/version/temperature/seed/prompt hash fields.
  - Definition of Done: Missing determinism metadata fails validation; populated metadata passes.
  - Scope: MVP.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Ensure docs, command examples, and MVP boundaries are explicit and executable.

- [X] T025 [P] Update execution and architecture docs in `README.md` and `specs/001-design-modular-resumable/quickstart.md`
  - Inputs: Completed MVP CLI and stage behavior.
  - Outputs: Accurate run examples, dependency behavior, skip rules, and MVP vs deferred notes.
  - Definition of Done: Docs match implemented commands and include at least one successful end-to-end run path.
  - Scope: MVP.

- [X] T026 Validate end-to-end quickstart flow in `tests/integration/test_quickstart_flow.py`
  - Inputs: All implemented stages, manifest, and sample fixtures.
  - Outputs: End-to-end regression test (`ingest -> clean -> enrich -> normalize-hashtags -> analyze`) with resume scenario.
  - Definition of Done: Test verifies independent stage execution, artifact reuse, and traceable outputs.
  - Scope: MVP.

- [X] T027 [P] Capture deferred extension backlog in `specs/001-design-modular-resumable/tasks.md` (deferred notes section)
  - Inputs: `research.md` Future scope decisions.
  - Outputs: Explicit deferred items (human review UI, remote artifact store, multi-agent adjudication, scheduler adapters).
  - Definition of Done: Deferred work is documented separately from MVP done criteria.
  - Scope: Deferred.

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1 → Phase 2 → Phase 3 (US1) → Phase 4 (US2) → Phase 5 (US3) → Phase 6.
- US2 depends on US1 runner integration for meaningful manifest entries.
- US3 depends on US1 stage framework and US2 manifest persistence.

### User Story Completion Order

1. **US1 (P1)**: independent stage execution + dependency validation + skip logic.
2. **US2 (P2)**: artifact lineage and manifest inspection.
3. **US3 (P3)**: agentic hashtag normalization and downstream integration.

### Within Each User Story

- Implement contracts/models before orchestration wiring.
- Wire CLI/stage integration before validation tests.
- Run story independent test before moving to next story.

## Parallel Execution Examples

### US1

```bash
# Parallelizable after T010 is complete:
Task T011: Implement deterministic stage modules
Task T012: Implement dependency subset validation
```

### US2

```bash
# Parallelizable after T016 is complete:
Task T018: Expose manifest inspection CLI
Task T019: Add manifest contract tests
```

### US3

```bash
# Parallelizable after T021 is complete:
Task T022: Persist/reload agent outputs
Task T023: Integrate normalized hashtags into analysis
```

## Implementation Strategy

### MVP First (Recommended)

1. Complete Phase 1 and Phase 2 foundations.
2. Deliver US1 (T010-T015) and validate independent rerun behavior.
3. Add US2 (T016-T019) for lineage/audit compliance.
4. Add US3 (T020-T024) for agentic equivalence loop and downstream use.
5. Finish with Phase 6 validation and docs.

### Incremental Delivery

- **Increment A**: Foundation + US1 (core modular pipeline MVP).
- **Increment B**: US2 (artifact governance and inspection).
- **Increment C**: US3 (agentic normalization and integration).

## Deferred Notes (Non-MVP)

- Human review UI/work queues for `pending_review` decisions.
- External object store / remote manifest registry.
- Multi-agent adjudication and confidence calibration strategies.
- Scheduler/event-driven execution adapters.
