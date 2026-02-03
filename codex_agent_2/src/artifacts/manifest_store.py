from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path

from src.artifacts.schemas.manifest import ArtifactRecord, PipelineManifest, StageRunRecord


class ManifestStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> PipelineManifest:
        if not self.path.exists():
            return PipelineManifest()
        return PipelineManifest.model_validate_json(self.path.read_text())

    def save(self, manifest: PipelineManifest) -> None:
        manifest.updated_at = datetime.now(UTC)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(manifest.model_dump_json(indent=2))

    def append_run(self, record: StageRunRecord) -> None:
        manifest = self.load()
        manifest.runs.append(record)
        self.save(manifest)

    def upsert_run(self, run_id: str, **updates) -> None:
        manifest = self.load()
        for idx, run in enumerate(manifest.runs):
            if run.run_id == run_id:
                merged = run.model_copy(update=updates)
                manifest.runs[idx] = merged
                self.save(manifest)
                return
        raise KeyError(f"Run not found: {run_id}")

    def append_artifacts(self, artifacts: list[ArtifactRecord]) -> None:
        manifest = self.load()
        manifest.artifacts.extend(artifacts)
        self.save(manifest)

    def latest_run_for_stage(self, stage_name: str) -> StageRunRecord | None:
        manifest = self.load()
        for run in reversed(manifest.runs):
            if run.stage_name == stage_name:
                return run
        return None

    def dump(self) -> dict:
        return json.loads(self.load().model_dump_json())
