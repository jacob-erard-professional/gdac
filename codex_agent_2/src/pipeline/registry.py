from __future__ import annotations

import hashlib
from pathlib import Path

from src.artifacts.schemas.manifest import ArtifactRecord


def sha256_file(path: str) -> str:
    data = Path(path).read_bytes()
    return hashlib.sha256(data).hexdigest()


def build_artifact_record(
    artifact_id: str,
    artifact_type: str,
    schema_version: str,
    path: str,
    produced_by_stage: str,
    lineage: dict | None = None,
) -> ArtifactRecord:
    return ArtifactRecord(
        artifact_id=artifact_id,
        artifact_type=artifact_type,
        schema_version=schema_version,
        path=path,
        checksum=sha256_file(path),
        produced_by_stage=produced_by_stage,
        lineage=lineage or {},
    )
