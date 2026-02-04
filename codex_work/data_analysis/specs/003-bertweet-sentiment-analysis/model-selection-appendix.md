# Model Selection Appendix — BERTweet Sentiment Analysis

## Purpose
Defines exactly which pretrained model(s) may be used for sentiment analysis of
tweet text, to ensure reproducibility and prevent silent model drift.

## Primary Model (Default)

Model identifier:
- `finiteautomata/bertweet-base-sentiment-analysis`

Model type:
- BERTweet-based sentiment classifier

Task:
- Tweet sentiment classification

Training:
- Fine-tuned on Twitter sentiment data (SemEval-style)

Supported labels:
- `negative`
- `neutral`
- `positive`

These are typically exposed as `NEG`, `NEU`, `POS`, but the implementation
must read them from `model.config.id2label`.

Label mapping:
- Must be obtained programmatically; do not hard-code any label indices.

Justification:
- Uses the BERTweet base model pretrained on English tweets.
- Has a sentiment head already trained for English tweet classification.
- Works well as a drop-in classifier for short, informal text.

## Tokenizer Requirement
- Load the tokenizer from the same checkpoint.
- Use `use_fast=False` for consistency.

## Fallback Model (Only If Default Fails)

Model identifier:
- `rabindralamsal/finetuned-bertweet-sentiment-analysis`

Notes:
- Alternative sentiment-fine-tuned BERTweet model on Hugging Face.
- Use only if the primary fails to load.

## Disallowed Models
- Generic BERT sentiment models not trained on tweets
- RoBERTa models without Twitter pretraining
- Any model without a sentiment classification head

## Model Substitution Rules
- Silent substitution is forbidden.
- Fallback use must be explicitly logged.

## Versioning
- Record the full model identifier and commit hash (if available) in output
  metadata to allow exact reproducibility.

## Limitations
- Model may exhibit bias and domain drift
- Sarcasm and memes may be misclassified
