# Specify.Tasks — Pretrained BERTweet Sentiment Analysis

## Scope
These tasks govern implementation of a deterministic sentiment analysis pipeline
step using a pretrained, sentiment-finetuned BERTweet model.

This task list explicitly excludes:
- Agentic workflows
- Model training or fine-tuning
- External APIs or hosted inference
- Any modification to upstream data ingestion or cleaning

## Phase 0 — Model Selection & Lock-in

### T000: Add model selection appendix
- Select a single pretrained BERTweet sentiment checkpoint as default
- Document:
  - model identifier
  - training dataset/task
  - supported labels
  - label ordering (`id2label`)
- Define acceptable fallback models (if default fails to load)
- Explicitly forbid automatic model substitution

## Phase 1 — Environment & Dependencies

### T001: Verify runtime dependencies
- Confirm Python version compatibility
- Confirm `torch` and `transformers` availability
- Confirm CPU-only execution is supported

### T002: Define configuration surface
- model identifier
- batch size
- input data location (year or directory)
- output location
- dry-run flag

## Phase 2 — Data Interface

### T003: Define sentiment input contract
- Required fields: `tweet_id`, `text`, `year`
- Supported file formats (CSV / Parquet)
- Validation for missing or malformed rows

### T004: Implement minimal tweet preprocessing
- URL removal
- whitespace normalization
- no additional text normalization permitted

## Phase 3 — Model Loading

### T005: Implement tokenizer loading
- Load tokenizer from model checkpoint
- Enforce `use_fast=False`
- Validate tokenizer compatibility

### T006: Implement model loading
- Load `AutoModelForSequenceClassification`
- Set model to eval mode
- Validate presence of `id2label` mapping
- Validate required sentiment labels exist

## Phase 4 — Inference

### T007: Implement batch tokenization
- Padding enabled
- Truncation enabled
- Max length = 128

### T008: Implement batch inference
- `torch.no_grad` context
- softmax over logits
- argmax label selection
- confidence extraction from probabilities

### T009: Implement batch iteration logic
- Configurable batch size
- Deterministic processing order
- Graceful handling of empty batches

## Phase 5 — Output Generation

### T010: Define sentiment output schema
- `tweet_id`
- `year`
- `sentiment`
- `confidence`

### T011: Implement output writer
- Year-partitioned output directories
- Deterministic filenames
- JSON or Parquet output

## Phase 6 — CLI Integration

### T012: Implement sentiment CLI entrypoint
- Accept year or input directory
- Accept model identifier override
- Accept batch size override
- Support dry-run mode

### T013: Integrate optional pipeline hook
- Enable sentiment step via pipeline flag
- Ensure no default behavior changes upstream

## Phase 7 — Validation & Safety

### T014: Implement runtime validation checks
- Model/tokenizer load success
- Label mapping sanity check
- Output schema consistency

### T015: Implement minimal smoke tests
- Single tweet inference
- Small batch inference
- Invalid input handling

## Phase 8 — Documentation

### T016: Update README documentation
- Model choice rationale
- Preprocessing decisions
- How to run sentiment analysis
- Output interpretation
- Known limitations (sarcasm, domain drift)

## Success Criteria
- Deterministic outputs for identical inputs
- Reproducible yearly runs
- No hidden model changes
- Clear audit trail from input tweet to sentiment output
