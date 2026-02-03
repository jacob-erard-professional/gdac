from __future__ import annotations

import json
from pathlib import Path

from src.pipeline.orchestrator import Orchestrator


def test_agent_determinism_metadata_logged(tmp_path: Path):
    manifest_path = tmp_path / "manifest.json"
    cfg = tmp_path / "normalize.yaml"
    cfg.write_text("iteration: 1\nprompt:\n  task: normalize\n")

    candidates = [
        {
            "candidate_id": "c1",
            "tag": "#SuperBowl",
            "normalized_token": "#superbowl",
            "frequency": 1,
            "contexts": ["#SuperBowl #SB54"],
        }
    ]
    candidates_path = tmp_path / "hashtags.json"
    candidates_path.write_text(json.dumps(candidates))
    output_path = tmp_path / "mappings.json"

    orchestrator = Orchestrator(str(manifest_path))
    result = orchestrator.run_stage(
        "normalize-hashtags",
        [str(candidates_path)],
        [str(output_path)],
        str(cfg),
        False,
    )
    assert result["status"] == "succeeded"

    manifest = json.loads(manifest_path.read_text())
    run = manifest["runs"][-1]
    determinism = run["determinism"]
    assert determinism["mode"] == "non_deterministic"
    for key in ["model_provider", "model", "model_version", "temperature", "seed", "prompt_hash"]:
        assert key in determinism
