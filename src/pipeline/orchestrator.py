from __future__ import annotations

import hashlib
import importlib
import json
from datetime import datetime, UTC
from pathlib import Path
from uuid import uuid4

import yaml

from src.artifacts.manifest_store import ManifestStore
from src.artifacts.schemas.manifest import DeterminismMetadata, RunStatus, StageRunRecord
from src.artifacts.validator import VALIDATION_CODES, outputs_exist, validation_error
from src.pipeline.dependencies import DependencyValidationError, get_stage, validate_selected_subset
from src.pipeline.registry import build_artifact_record


class Orchestrator:
    def __init__(self, manifest_path: str = "artifacts/manifest.json"):
        self.manifest = ManifestStore(manifest_path)

    def _load_config(self, path: str) -> dict:
        cfg_path = Path(path)
        if not cfg_path.exists():
            return {}
        if cfg_path.suffix in {".yaml", ".yml"}:
            return yaml.safe_load(cfg_path.read_text()) or {}
        return json.loads(cfg_path.read_text())

    def _hash_config(self, config_path: str) -> str:
        content = Path(config_path).read_bytes() if Path(config_path).exists() else b""
        return hashlib.sha256(content).hexdigest()

    def _load_runner(self, runner_ref: str):
        module_name, function_name = runner_ref.split(":")
        module = importlib.import_module(module_name)
        return getattr(module, function_name)

    def should_skip_stage(self, stage_name: str, output_paths: list[str]) -> bool:
        latest = self.manifest.latest_run_for_stage(stage_name)
        if not latest:
            return False
        if latest.status != RunStatus.succeeded:
            return False
        if not outputs_exist(output_paths):
            return False
        return True

    def run_stage(
        self,
        stage_name: str,
        input_paths: list[str],
        output_paths: list[str],
        config_path: str,
        dry_run: bool,
        skip_completed: bool = False,
        event: str | None = None,
        year: int | None = None,
    ) -> dict:
        stage = get_stage(stage_name)
        if skip_completed and self.should_skip_stage(stage_name, output_paths):
            return {"status": "skipped", "stage": stage_name}

        run_id = f"run-{uuid4()}"
        cfg_hash = self._hash_config(config_path)
        run_record = StageRunRecord(
            run_id=run_id,
            stage_name=stage_name,
            event=event,
            year=year,
            status=RunStatus.started,
            config_hash=cfg_hash,
            input_artifact_ids=input_paths,
            output_artifact_ids=output_paths,
            determinism=DeterminismMetadata(mode="deterministic"),
        )
        self.manifest.append_run(run_record)

        runner = self._load_runner(stage.runner)
        config = self._load_config(config_path)

        try:
            result = runner(input_paths, output_paths, config, dry_run)
            status = RunStatus.skipped if result.get("status") == "dry_run" else RunStatus.succeeded
            determinism = {
                "mode": result.get("determinism_mode", "deterministic"),
                "model_provider": result.get("model_provider"),
                "model": result.get("model"),
                "model_version": result.get("model_version"),
                "temperature": result.get("temperature"),
                "seed": result.get("seed"),
                "prompt_hash": result.get("prompt_hash"),
            }
            self.manifest.upsert_run(
                run_id,
                status=status,
                end_time=datetime.now(UTC),
                determinism=DeterminismMetadata(**determinism),
            )

            if not dry_run and status == RunStatus.succeeded:
                artifacts = []
                for idx, path in enumerate(output_paths, start=1):
                    artifacts.append(
                        build_artifact_record(
                            artifact_id=f"{run_id}-out-{idx}",
                            artifact_type=stage_name,
                            schema_version=result.get("schema_version", "1.0.0"),
                            path=path,
                            produced_by_stage=stage_name,
                            lineage={"inputs": input_paths},
                        )
                    )
                self.manifest.append_artifacts(artifacts)
            return {"status": status, "run_id": run_id, "result": result}
        except Exception as exc:  # noqa: BLE001
            self.manifest.upsert_run(
                run_id,
                status=RunStatus.failed,
                end_time=datetime.now(UTC),
                error={"message": str(exc)},
            )
            raise

    def run_many(
        self,
        stage_names: list[str],
        input_paths: list[str],
        output_root: str,
        config_path: str,
        skip_completed: bool,
        dry_run: bool,
        event: str | None = None,
        year: int | None = None,
    ) -> dict:
        try:
            validate_selected_subset(stage_names)
        except DependencyValidationError as exc:
            raise ValueError(
                validation_error(
                    code=VALIDATION_CODES["dependency"],
                    message="Selected stages violate dependency declarations",
                    stage="run-many",
                    artifact_path=output_root,
                    schema_version="1.0.0",
                    details={"missing": exc.missing},
                )
            ) from exc

        results = []
        last_output = input_paths
        for stage_name in stage_names:
            output_path = str(Path(output_root) / stage_name / f"{stage_name}.json")
            result = self.run_stage(
                stage_name=stage_name,
                input_paths=last_output,
                output_paths=[output_path],
                config_path=config_path,
                dry_run=dry_run,
                skip_completed=skip_completed,
                event=event,
                year=year,
            )
            results.append(result)
            last_output = [output_path]
        return {"results": results}
