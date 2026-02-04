from src.agents.sentiment.schemas.agent_outputs import EmotionOutput, PolarityOutput, SarcasmOutput
from src.agents.sentiment.schemas.final_record import FinalSentiment
from src.agents.sentiment.supervisor.flags import derive_flags


def adjudicate_final(
    polarity: PolarityOutput,
    emotion: EmotionOutput,
    sarcasm: SarcasmOutput,
) -> tuple[FinalSentiment, list[str]]:
    sentiment = polarity.sentiment
    confidence = (polarity.confidence * 0.7) + (emotion.confidence * 0.2) + (sarcasm.confidence * 0.1)

    if sarcasm.is_sarcastic and sarcasm.confidence >= 0.6:
        # Conservative adjustment to avoid over-claiming polarity under sarcasm uncertainty.
        if sentiment != "neutral":
            sentiment = "neutral"
            confidence = max(0.35, confidence - 0.2)

    flags = derive_flags(polarity, emotion, sarcasm, confidence)
    return FinalSentiment(sentiment=sentiment, confidence=round(confidence, 4)), flags

