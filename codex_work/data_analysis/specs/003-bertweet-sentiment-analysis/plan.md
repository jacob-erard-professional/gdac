# Implementation Plan — Pretrained BERTweet Sentiment Analysis

## Objective
Implement a deterministic, non-agentic sentiment analysis step using an
existing, pretrained BERTweet model with a sentiment classification head.

This implementation requires no model training or fine-tuning and operates as
batch inference over cleaned X (Twitter) data.

The implementation is intended to be invoked via CLI and to integrate cleanly
into the existing yearly data pipeline.

## Fixed Technical Choices
The following choices are mandatory and must not be substituted:

- Framework: PyTorch
- Model loading: Hugging Face Transformers
- Model type: `AutoModelForSequenceClassification`
- Tokenizer type: BERTweet-compatible tokenizer
- Inference only (no training loops)
- Pretrained, sentiment-finetuned BERTweet checkpoint
- Batch inference only (no per-row inference)

## Required Tools / Dependencies
The implementation assumes the following Python packages are available:

- `python >= 3.10`
- `torch`
- `transformers`
- `pandas` (for CSV handling)
- `numpy` (optional but allowed)

No other ML frameworks (TensorFlow, JAX) are permitted.

No external APIs, OpenRouter, LangChain, or online inference services are to be
used for this implementation.

## Model Requirements
- The model must be loaded from a public pretrained checkpoint that includes a
  sentiment classification head.
- The model must support at least the following labels:
  - `positive`
  - `neutral`
  - `negative`
- The model label mapping (`id2label`) must be read programmatically and not
  hard-coded.

## Tokenizer Requirements
- The tokenizer must be loaded from the same checkpoint as the model.
- The tokenizer must be instantiated with `use_fast=False`.
- Tokenization must use:
  - `padding=True`
  - `truncation=True`
  - `max_length=128`

## Preprocessing Requirements
Tweet text preprocessing must be minimal and Twitter-aware.

Required:
- Remove URLs
- Normalize whitespace

Prohibited:
- Removing emojis
- Removing hashtags
- Lowercasing text manually
- Removing punctuation aggressively
- Expanding slang via dictionaries

## Inference Requirements
- Inference must be performed under `torch.no_grad()`.
- Softmax must be applied to model logits to obtain probabilities.
- Sentiment label must be chosen via argmax over probabilities.
- Confidence must be the max probability for the selected label.

## Batching Requirements
- Tweets must be processed in batches.
- Batch size must be configurable via CLI or config.
- Single-tweet inference is not permitted except in test cases.

## Input Contract
The sentiment step consumes cleaned tweet data produced by the core pipeline.

Minimum required fields:
- `tweet_id` (string or int)
- `text` (string)
- `year` (int)

Input format:
- CSV or Parquet
- One tweet per row

## Output Contract
The sentiment step must emit one output record per input tweet.

Minimum required output fields:
- `tweet_id`
- `year`
- `sentiment` (`positive | neutral | negative`)
- `confidence` (float `0.0–1.0`)

Output format:
- JSON or Parquet
- Deterministic ordering
- Year-partitioned output directory

## Output Location
Outputs must be written to a dedicated sentiment directory, partitioned by
year.

Example:

```text
sentiment/
└── bertweet/
    └── 2024/
        └── sentiment.json
```

## CLI Requirements
A CLI entrypoint must be provided with the following capabilities:

- Accept a year OR a data directory as input
- Accept a model identifier (defaulting to the chosen BERTweet checkpoint)
- Accept batch size configuration
- Support a dry-run mode
- Emit progress logging

## Integration Requirements
- This step must be runnable independently.
- This step must be optionally invokable from the full pipeline via a flag.
- No upstream pipeline behavior may be altered by default.

## Validation Requirements
The implementation must validate that:
- Model and tokenizer load successfully
- Label mapping contains required sentiment labels
- Output schema is consistent for all records

## Documentation Requirements
The repository README must be updated to document:

- Why BERTweet was chosen
- Model limitations
- Preprocessing choices
- How to run the sentiment step
- Expected outputs

## Non-goals
- No agentic workflows
- No LLM orchestration
- No fine-tuning
- No real-time inference
- No API services

## Success Criteria
- Deterministic sentiment outputs for identical inputs
- Reproducible yearly runs
- Clear, auditable sentiment results
- Minimal configuration surface
- Easy future extension to agentic workflows
