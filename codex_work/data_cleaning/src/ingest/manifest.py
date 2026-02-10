from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def build_file_hashes(paths: List[Path]) -> List[Dict[str, str]]:
    return [{"path": str(path), "sha256": sha256_file(path)} for path in paths]


def emit_manifest(
    output_path: Path,
    step_name: str,
    run_id: str,
    input_files: List[Path],
    output_files: List[Path],
    rows_in: int,
    rows_out: int,
    rows_rejected: int,
    rejection_reasons: Dict[str, int],
    agent_metadata: Dict[str, str] | None = None,
) -> Path:
    manifest = {
        "step_name": step_name,
        "run_id": run_id,
        "input_files": build_file_hashes(input_files),
        "output_files": build_file_hashes(output_files),
        "rows_in": rows_in,
        "rows_out": rows_out,
        "rows_rejected": rows_rejected,
        "rejection_reasons": rejection_reasons,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "agent_metadata": agent_metadata or {},
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return output_path
