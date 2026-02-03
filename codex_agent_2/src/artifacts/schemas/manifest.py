from __future__ import annotations

from datetime import datetime, UTC
from enum import Enum

from pydantic import BaseModel, Field, field_validator


def now_utc() -> datetime:
    return datetime.now(UTC)


class RunStatus(str, Enum):
    started = "started"
    succeeded = "succeeded"
    failed = "failed"
    skipped = "skipped"


class DeterminismMetadata(BaseModel):
    mode: str = Field(pattern=r"^(deterministic|non_deterministic)$")
    model_provider: str | None = None
    model: str | None = None
    model_version: str | None = None
    temperature: float | None = None
    seed: int | None = None
    prompt_hash: str | None = None


class ArtifactRecord(BaseModel):
    artifact_id: str
    artifact_type: str
    schema_version: str
    path: str
    checksum: str = Field(pattern=r"^[a-f0-9]{64}$")
    created_at: datetime = Field(default_factory=now_utc)
    produced_by_stage: str
    lineage: dict | None = None


class StageRunRecord(BaseModel):
    run_id: str
    stage_name: str
    event: str | None = None
    year: int | None = None
    status: RunStatus
    start_time: datetime = Field(default_factory=now_utc)
    end_time: datetime | None = None
    config_hash: str
    input_artifact_ids: list[str]
    output_artifact_ids: list[str]
    error: dict | None = None
    determinism: DeterminismMetadata

    @field_validator("end_time")
    @classmethod
    def terminal_requires_end_time(cls, value: datetime | None, info):
        status = info.data.get("status")
        if status in {RunStatus.succeeded, RunStatus.failed, RunStatus.skipped} and value is None:
            raise ValueError("Terminal statuses require end_time")
        return value


class StageDefinitionRecord(BaseModel):
    name: str
    dependencies: list[str]
    input_schema_versions: list[str]
    output_schema_versions: list[str]


class PipelineManifest(BaseModel):
    manifest_version: str = "1.0.0"
    pipeline_name: str = "nlp-analytics"
    updated_at: datetime = Field(default_factory=now_utc)
    stages: list[StageDefinitionRecord] = Field(default_factory=list)
    runs: list[StageRunRecord] = Field(default_factory=list)
    artifacts: list[ArtifactRecord] = Field(default_factory=list)
