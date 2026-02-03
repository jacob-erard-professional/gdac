from __future__ import annotations

import json
from pathlib import Path

from src.pipeline.orchestrator import Orchestrator


def test_rerun_stage_without_side_effects(tmp_path: Path):
    manifest_path = tmp_path / "manifest.json"
    data_file = tmp_path / "posts.jsonl"
    data_file.write_text('{"id": 1, "text": "Hello #Tag"}\n')
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("{}\n")

    orchestrator = Orchestrator(str(manifest_path))

    ingest_out = tmp_path / "ingest.jsonl"
    clean_out = tmp_path / "clean.jsonl"
    first = orchestrator.run_stage("ingest", [str(data_file)], [str(ingest_out)], str(cfg), False)
    assert first["status"] == "succeeded"

    second = orchestrator.run_stage("ingest", [str(data_file)], [str(ingest_out)], str(cfg), False)
    assert second["status"] == "succeeded"

    clean = orchestrator.run_stage("clean", [str(ingest_out)], [str(clean_out)], str(cfg), False)
    assert clean["status"] == "succeeded"
    first_clean_payload = clean_out.read_text()

    rerun_clean = orchestrator.run_stage("clean", [str(ingest_out)], [str(clean_out)], str(cfg), False)
    assert rerun_clean["status"] == "succeeded"
    assert clean_out.read_text() == first_clean_payload
