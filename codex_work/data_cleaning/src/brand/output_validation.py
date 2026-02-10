from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from pydantic import ValidationError

from src.brand.agent_schemas import AgentOutput


def validate_outputs(outputs: List[Dict[str, Any]]) -> Tuple[List[AgentOutput], List[Dict[str, Any]]]:
    valid: List[AgentOutput] = []
    invalid: List[Dict[str, Any]] = []
    for payload in outputs:
        try:
            valid.append(AgentOutput.model_validate(payload))
        except ValidationError as exc:
            invalid.append({"payload": payload, "error": str(exc)})
    return valid, invalid


def quarantine_invalid_outputs(invalid: List[Dict[str, Any]], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "agent_output_quarantine.json"
    path.write_text(json.dumps(invalid, indent=2, sort_keys=True), encoding="utf-8")
    return path
