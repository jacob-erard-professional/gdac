from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class RunManifest:
    input_files: List[str]
    output_files: List[str]
    record_counts: Dict[str, int]
    started_at: str
    completed_at: str
    notes: List[str] = field(default_factory=list)


@dataclass
class StageResult:
    stage: str
    status: str  # success | failed | skipped
    metadata: RunManifest
