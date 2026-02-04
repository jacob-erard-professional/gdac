from src.agents.sentiment.schemas.agent_outputs import EmotionOutput, NormalizerOutput, PolarityOutput, SarcasmOutput
from src.agents.sentiment.schemas.final_record import SentimentRecord, SentimentSummary


def validate_agent_payloads(payloads: dict) -> dict:
    return {
        "normalizer": NormalizerOutput.model_validate(payloads["normalizer"]),
        "polarity": PolarityOutput.model_validate(payloads["polarity"]),
        "emotion": EmotionOutput.model_validate(payloads["emotion"]),
        "sarcasm": SarcasmOutput.model_validate(payloads["sarcasm"]),
    }


def validate_record(record: dict) -> SentimentRecord:
    return SentimentRecord.model_validate(record)


def validate_summary(summary: dict) -> SentimentSummary:
    return SentimentSummary.model_validate(summary)

