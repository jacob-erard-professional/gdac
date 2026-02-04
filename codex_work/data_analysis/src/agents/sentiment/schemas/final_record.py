from pydantic import BaseModel, Field
from typing import Literal

from .agent_outputs import EmotionOutput, NormalizerOutput, PolarityOutput, SarcasmOutput


class FinalSentiment(BaseModel):
    sentiment: Literal["positive", "neutral", "negative"]
    confidence: float = Field(ge=0.0, le=1.0)


class AgentPayloads(BaseModel):
    polarity: PolarityOutput
    emotion: EmotionOutput
    sarcasm: SarcasmOutput
    normalizer: NormalizerOutput


class SentimentRecord(BaseModel):
    tweet_id: str
    year: int
    final: FinalSentiment
    agents: AgentPayloads
    flags: list[str] = Field(default_factory=list)


class SentimentSummary(BaseModel):
    year: int
    total_tweets: int
    sentiment_counts: dict[str, int]
    emotion_counts: dict[str, int]
    sarcasm_rate: float = Field(ge=0.0, le=1.0)
    low_confidence_count: int

