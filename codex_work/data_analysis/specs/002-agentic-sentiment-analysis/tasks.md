# Tasks: Agentic Sentiment Analysis for X (Twitter) Data

**Input**: Design documents from `specs/002-agentic-sentiment-analysis/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

## Phase 1 - Foundations

- [ ] T001 Define sentiment output schemas in `src/agents/sentiment/schemas/agent_outputs.py` and `src/agents/sentiment/schemas/final_record.py`
- [ ] T002 Establish sentiment module directory structure under `src/agents/sentiment/{agents,supervisor,prompts,schemas}/` and `src/cli/sentiment.py`
- [ ] T003 Implement model configuration abstraction in `src/agents/sentiment/config.py` (OpenRouter compatibility, per-agent model selection, centralized key handling)

## Phase 2 - Core Agents

- [ ] T004 Implement Normalizer Agent in `src/agents/sentiment/agents/normalizer.py` (emoji/slang normalization, URL and username stripping, JSON-only output)
- [ ] T005 Implement Polarity Agent in `src/agents/sentiment/agents/polarity.py` (positive/neutral/negative, confidence, rationale)
- [ ] T006 Implement Emotion Agent in `src/agents/sentiment/agents/emotion.py` (fixed taxonomy, single label, confidence)
- [ ] T007 Implement Sarcasm Detection Agent in `src/agents/sentiment/agents/sarcasm.py` (binary sarcasm flag, confidence, conservative bias)

## Phase 3 - Orchestration

- [ ] T008 Implement parallel agent execution in `src/agents/sentiment/orchestrator.py` using LangChain `RunnableParallel` (or equivalent)
- [ ] T009 Implement Supervisor Agent in `src/agents/sentiment/supervisor/supervisor.py` (conflict resolution, final decision, calibrated confidence)
- [ ] T010 Implement ambiguity and confidence flagging in `src/agents/sentiment/supervisor/flags.py` (low confidence threshold, sarcasm-aware adjudication)

## Phase 4 - CLI and Pipeline Integration

- [ ] T011 Implement CLI entrypoint in `src/cli/sentiment.py` (year/data-dir input, dry-run, verbose/debug)
- [ ] T012 Integrate optional sentiment step into pipeline in `src/pipeline/orchestrator.py` and `src/cli/run.py` via `--with-sentiment`
- [ ] T013 Implement deterministic artifact writing in `src/agents/sentiment/writer.py` for `outputs/analytics/<year>/sentiment_agentic.jsonl` and `outputs/analytics/<year>/sentiment_agentic_summary.json`

## Phase 5 - Validation and Documentation

- [ ] T014 Validate schema conformance in `src/agents/sentiment/validation.py` with fail-fast behavior for malformed outputs
- [ ] T015 Update sentiment documentation in `README.md` (agent roles, model choices, execution, limitations, cost guidance)
- [ ] T016 Add smoke tests in `tests/integration/test_sentiment_agentic_smoke.py` and `tests/unit/test_sentiment_supervisor_conflicts.py`

## Deferred (Post-MVP)

- [ ] D001 Topic inference agent
- [ ] D002 Ensemble voting strategies
- [ ] D003 Cross-year language drift analysis
- [ ] D004 Human-in-the-loop review hooks
