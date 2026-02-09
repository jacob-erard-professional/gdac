# Tasks: Agentic Emotion Classification

**Input**: `specs/007-agentic-emotion-classification/spec.md`  
**Prerequisites**: plan.md (required), spec.md (required)

## Phase 1: Foundations

- [ ] T001 Define emotion taxonomy and constraints
  - Enumerate allowed emotions
  - Define neutral / no-emotion semantics
- [ ] T002 Define JSON schemas for all agent outputs
  - Enforce strict machine-readable formats

## Phase 2: Agent Implementation

- [ ] T003 Implement Emotion Presence Agent
  - Output: emotional | neutral | uncertain
  - Include confidence score
- [ ] T004 Implement Polarity Agent
  - Output: positive | negative | neutral
- [ ] T005 Implement Emotion Classifier Agent
  - Outputs candidate emotion + confidence
  - Must not emit neutral
- [ ] T006 Implement Sarcasm / Irony Agent
  - Output: sarcastic | not_sarcastic
  - Conservative bias required

## Phase 3: Supervision

- [ ] T007 Implement Supervisor Agent
  - Consumes all agent outputs
  - Applies reasoning to:
    - Abstain to neutral when evidence is weak
    - Override emotion when sarcasm is present
    - Enforce taxonomy constraints
- [ ] T008 Implement confidence calibration logic
  - Downgrade confidence when agents disagree

## Phase 4: Brand-level Aggregation

- [ ] T009 Link emotion outputs to brand identifiers
  - One brand per tweet
- [ ] T010 Implement example selection logic
  - Select top-N highest-confidence tweets per brand + emotion
  - Exclude low-confidence or ambiguous cases

## Phase 5: CLI & Pipeline Integration

- [ ] T011 Implement CLI entrypoint
  - Accept year or dataset
  - Accept brand filter
  - Support dry-run mode
- [ ] T012 Integrate optional pipeline hook
  - Must not run by default

## Phase 6: Validation & Documentation

- [ ] T013 Validate schema compliance
  - All agent outputs
  - Final outputs
- [ ] T014 Add README documentation
  - Emotion definitions
  - Agent roles
  - Example interpretation guidance

