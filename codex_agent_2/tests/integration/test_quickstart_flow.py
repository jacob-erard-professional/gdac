from __future__ import annotations

import json
from pathlib import Path

from src.pipeline.orchestrator import Orchestrator


def test_end_to_end_quickstart_flow(tmp_path: Path):
    manifest_path = tmp_path / "manifest.json"
    orchestrator = Orchestrator(str(manifest_path))

    raw = tmp_path / "posts.jsonl"
    raw.write_text('{"id": 1, "text": "Game day #SuperBowl #SB54"}\n')
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("{}\n")

    ingest_out = tmp_path / "ingest.jsonl"
    clean_out = tmp_path / "clean.jsonl"
    enrich_out = tmp_path / "hashtags.json"
    normalize_cfg = tmp_path / "normalize.yaml"
    normalize_cfg.write_text("iteration: 1\nprompt:\n  task: normalize\n")
    mappings_out = tmp_path / "mappings.json"
    analyze_cfg = tmp_path / "analyze.yaml"
    analyze_cfg.write_text(f"normalized_mappings_path: {mappings_out}\n")
    analyze_out = tmp_path / "report.json"

    assert orchestrator.run_stage("ingest", [str(raw)], [str(ingest_out)], str(cfg), False)["status"] == "succeeded"
    assert orchestrator.run_stage("clean", [str(ingest_out)], [str(clean_out)], str(cfg), False)["status"] == "succeeded"
    assert orchestrator.run_stage("enrich", [str(clean_out)], [str(enrich_out)], str(cfg), False)["status"] == "succeeded"
    assert (
        orchestrator.run_stage("normalize-hashtags", [str(enrich_out)], [str(mappings_out)], str(normalize_cfg), False)["status"]
        == "succeeded"
    )
    assert (
        orchestrator.run_stage("analyze", [str(enrich_out)], [str(analyze_out)], str(analyze_cfg), False)["status"]
        == "succeeded"
    )

    report = json.loads(analyze_out.read_text())
    assert report["total_unique_hashtags"] >= 1

    # Resume scenario: skip completed selected stages.
    many_cfg = tmp_path / "many.yaml"
    many_cfg.write_text(f"normalized_mappings_path: {mappings_out}\n")
    rerun = orchestrator.run_many(
        ["clean", "enrich", "analyze"],
        [str(ingest_out)],
        str(tmp_path),
        str(many_cfg),
        skip_completed=True,
        dry_run=False,
    )
    assert "results" in rerun
