from __future__ import annotations

from datetime import datetime, UTC
from enum import Enum

from pydantic import BaseModel, Field


def now_utc() -> datetime:
    return datetime.now(UTC)


class MappingState(str, Enum):
    draft = "draft"
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"


class HashtagCandidate(BaseModel):
    candidate_id: str
    tag: str = Field(pattern=r"^#")
    normalized_token: str
    frequency: int = Field(ge=1)
    contexts: list[str] = Field(default_factory=list)


class EquivalenceClass(BaseModel):
    class_id: str
    canonical_tag: str
    members: list[str]
    aggregate_confidence: float = Field(ge=0.0, le=1.0)
    iteration: int = Field(ge=1)


class HashtagMapping(BaseModel):
    mapping_id: str
    raw_tag: str
    canonical_tag: str
    confidence: float = Field(ge=0.0, le=1.0)
    state: MappingState = MappingState.draft
    evidence: list[str] = Field(default_factory=list)
    agent_run_id: str
    created_at: datetime = Field(default_factory=now_utc)


class AgentTraceEntry(BaseModel):
    raw_tag: str
    canonical_tag: str
    reason: str


class HashtagNormalizationArtifact(BaseModel):
    iteration: int = Field(ge=1)
    equivalence_classes: list[EquivalenceClass]
    mappings: list[HashtagMapping]
    trace: list[AgentTraceEntry]
