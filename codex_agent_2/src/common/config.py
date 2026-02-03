from __future__ import annotations

import json
from pathlib import Path

import yaml


def load_config(path: str) -> dict:
    cfg_path = Path(path)
    if not cfg_path.exists():
        return {}
    if cfg_path.suffix in {'.yaml', '.yml'}:
        return yaml.safe_load(cfg_path.read_text()) or {}
    return json.loads(cfg_path.read_text())
