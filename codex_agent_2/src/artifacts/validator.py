from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from src.artifacts.schemas.manifest import PipelineManifest


VALIDATION_CODES = {
    "schema": "SCHEMA_MISMATCH",
    "missing": "MISSING_FIELD",
    "type": "TYPE_ERROR",
    "constraint": "CONSTRAINT_VIOLATION",
    "dependency": "DEPENDENCY_ERROR",
}


def validation_error(
    code: str,
    message: str,
    stage: str,
    artifact_path: str,
    schema_version: str,
    details: dict,
) -> dict:
    return {
        "code": code,
        "message": message,
        "stage": stage,
        "artifact_path": artifact_path,
        "schema_version": schema_version,
        "details": details,
    }


def validate_manifest_payload(payload: str, artifact_path: str = "artifacts/manifest.json") -> PipelineManifest:
    try:
        return PipelineManifest.model_validate_json(payload)
    except ValidationError as exc:
        raise ValueError(
            validation_error(
                code=VALIDATION_CODES["schema"],
                message="Manifest validation failed",
                stage="manifest",
                artifact_path=artifact_path,
                schema_version="1.0.0",
                details={"errors": exc.errors()},
            )
        ) from exc


def outputs_exist(paths: list[str]) -> bool:
    return all(Path(path).exists() for path in paths)
