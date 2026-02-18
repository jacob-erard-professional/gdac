"""Pipeline module for manifest orchestration and execution."""

import json
from dataclasses import asdict
from pathlib import Path
from .contracts import RunManifest


def write_manifest(path: Path, manifest: RunManifest) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(manifest), indent=2), encoding="utf-8")
