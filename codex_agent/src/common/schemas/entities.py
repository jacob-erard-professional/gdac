from dataclasses import dataclass


@dataclass(slots=True)
class PipelineRun:
    run_id: str
    event_name: str
    year: int
    status: str


@dataclass(slots=True)
class RawSocialRecord:
    source_record_id: str
    event_name: str
    year: int
    text: str


@dataclass(slots=True)
class CleanedSocialRecord:
    source_record_id: str
    event_name: str
    year: int
    normalized_text: str
    is_valid: bool
    rejection_reason: str | None = None


@dataclass(slots=True)
class EnrichedSocialRecord:
    source_record_id: str
    event_name: str
    year: int
    normalized_text: str
    event_phase: str = "event_day"


@dataclass(slots=True)
class YearlyKPIResult:
    run_id: str
    event_name: str
    year: int
    kpi_id: str
    value: float


@dataclass(slots=True)
class ArtifactIndexEntry:
    artifact_id: str
    artifact_type: str
    year: int
    file_path: str
