from dataclasses import dataclass, field


@dataclass(slots=True)
class ValidationReport:
    accepted_records: int = 0
    rejected_records: int = 0
    rejection_breakdown: dict[str, int] = field(default_factory=dict)


@dataclass(slots=True)
class StageResult:
    stage_name: str
    status: str
    duration_ms: int
    output_ref: str
    validation: ValidationReport = field(default_factory=ValidationReport)
