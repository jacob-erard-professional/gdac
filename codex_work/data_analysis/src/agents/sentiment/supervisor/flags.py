from src.agents.sentiment.schemas.agent_outputs import EmotionOutput, PolarityOutput, SarcasmOutput


def derive_flags(polarity: PolarityOutput, emotion: EmotionOutput, sarcasm: SarcasmOutput, confidence: float) -> list[str]:
    flags: list[str] = []
    if confidence < 0.55:
        flags.append("low_confidence")
    if sarcasm.is_sarcastic and sarcasm.confidence >= 0.6:
        flags.append("sarcasm_risk")
    if polarity.sentiment == "positive" and emotion.emotion in {"anger", "disappointment"}:
        flags.append("ambiguous")
    if polarity.sentiment == "negative" and emotion.emotion in {"joy", "excitement"}:
        flags.append("ambiguous")
    return flags

