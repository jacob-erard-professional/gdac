NORMALIZER_PROMPT = (
    "Normalize tweet text for sentiment analysis. Expand slang/emojis when clear, "
    "remove URLs and usernames, preserve sentiment-bearing words. "
    'Return strict JSON: {"normalized_text":"...","removed_tokens":[],"preserved_tokens":[],"rationale":"..."}'
)

POLARITY_PROMPT = (
    "Classify polarity as positive, neutral, or negative with confidence 0-1. "
    'Return strict JSON: {"sentiment":"positive|neutral|negative","confidence":0.0,"rationale":"..."}'
)

EMOTION_PROMPT = (
    "Classify primary emotion as joy, anger, disappointment, excitement, or neutral with confidence 0-1. "
    'Return strict JSON: {"emotion":"...","confidence":0.0,"rationale":"..."}'
)

SARCASM_PROMPT = (
    "Detect sarcasm or irony conservatively with confidence 0-1. "
    'Return strict JSON: {"is_sarcastic":true|false,"confidence":0.0,"rationale":"..."}'
)

SUPERVISOR_PROMPT = (
    "Resolve final sentiment based on polarity/emotion/sarcasm/normalized text. "
    "Calibrate confidence and provide flags when ambiguous or low confidence. "
    'Return strict JSON: {"sentiment":"positive|neutral|negative","confidence":0.0,"flags":[],"rationale":"..."}'
)

