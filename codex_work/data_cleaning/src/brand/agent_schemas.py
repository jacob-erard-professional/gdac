from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class AgentInput(BaseModel):
    input_id: str
    text_normalized: str
    brand_normalized: str
    brand_original: str
    prompt_version: str
    model: str
    router_model_params: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class AgentOutput(BaseModel):
    input_id: str
    brand_relevant: bool
    router_model_used: str
    prompt_version: str
    output_hash: str
    abstain: bool
    confidence: Optional[float] = None
    explanation: Optional[str] = None
    error: Optional[str] = None

    @field_validator("confidence")
    @classmethod
    def confidence_range(cls, value: Optional[float]) -> Optional[float]:
        if value is None:
            return value
        if not 0.0 <= value <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        return value

    @model_validator(mode="after")
    def enforce_abstention_rules(self) -> "AgentOutput":
        if self.abstain:
            if self.brand_relevant:
                raise ValueError("abstain outputs must not set brand_relevant true")
            if self.confidence not in (None, 0.0):
                raise ValueError("abstain outputs must not include confidence")
        if self.error and not self.abstain:
            raise ValueError("error must accompany abstain=true")
        return self


def parse_agent_output(payload: Dict[str, Any]) -> AgentOutput:
    return AgentOutput.model_validate(payload)
