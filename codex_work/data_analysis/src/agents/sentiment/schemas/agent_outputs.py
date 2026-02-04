from pydantic import BaseModel, Field
from typing import Literal


class NormalizerOutput(BaseModel):
    normalized_text: str
    removed_tokens: list[str] = Field(default_factory=list)
    preserved_tokens: list[str] = Field(default_factory=list)
    rationale: str = ""


class PolarityOutput(BaseModel):
    sentiment: Literal["positive", "neutral", "negative"]
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = ""


class EmotionOutput(BaseModel):
    emotion: Literal["joy", "anger", "disappointment", "excitement", "neutral"]
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = ""


class SarcasmOutput(BaseModel):
    is_sarcastic: bool
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = ""

