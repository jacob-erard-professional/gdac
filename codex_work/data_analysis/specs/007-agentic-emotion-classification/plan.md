# Specify Plan: Agentic Emotion Classification for Brand-Centric Tweet Analysis

**Branch**: `007-agentic-emotion-classification` | **Date**: 2026-02-07 | **Spec**: `specs/007-agentic-emotion-classification/spec.md`
**Input**: User-provided SPECIFY.PLAN for agentic emotion classification

## Purpose

Define an agentic workflow for classifying emotional expressions in brand-related tweets,
prioritizing precision and explainability. Primary outputs are emotion-labeled examples
per brand, not aggregate sentiment scores.

## Scope

**In scope**
- Multi-agent emotion classification
- Neutral / no-emotion detection
- Sarcasm and irony handling
- Brand-linked emotion attribution
- Example tweet extraction per emotion

**Out of scope**
- Real-time inference
- Model training or fine-tuning
- Opinion mining beyond tweet text
- Demographic or user profiling

## Design Principles

1. Precision over coverage
   - Prefer abstention over misclassification.
2. Neutral is first-class
   - No-strong-emotion must be explicitly detected.
3. Decomposition of judgment
   - Presence, polarity, sarcasm, and emotion type are distinct tasks.
4. Explainability
   - Every label must be justifiable via agent outputs.

## Agent Roles

1. **Emotion Presence Agent**
   - Outputs: emotional | neutral | uncertain
2. **Polarity Agent**
   - Outputs: positive | negative | neutral
3. **Emotion Classifier Agent**
   - Outputs candidate emotion (no neutral)
4. **Sarcasm / Irony Agent**
   - Outputs: sarcastic | not_sarcastic
5. **Supervisor (Arbiter) Agent**
   - Synthesizes all outputs into final label + confidence

## Emotion Taxonomy

Allowed emotions:
- joy
- excitement
- anger
- disappointment
- frustration
- sadness
- neutral (no strong emotion)

Additional emotions are disallowed without spec revision.

## Output Contracts

Per-tweet record:

```json
{
  "tweet_id": "<string>",
  "brand": "<string>",
  "final_emotion": "<emotion | neutral>",
  "confidence": <float>,
  "agent_evidence": {
    "emotion_presence": {...},
    "polarity": {...},
    "emotion_candidate": {...},
    "sarcasm": {...}
  }
}
```

Brand-level aggregation:

```json
{
  "brand": "<string>",
  "emotion": "<emotion>",
  "example_tweets": [
    { "tweet_id": "...", "text": "...", "confidence": ... }
  ]
}
```

## Integration Requirements

- Consume brand-tagged tweets from upstream pipeline
- Runnable per year or dataset
- Must not alter upstream brand mapping logic

## Documentation Requirements

README must cover:
- Rationale for agentic emotion classification
- Known failure modes
- Interpretation of labels
- Example selection logic

