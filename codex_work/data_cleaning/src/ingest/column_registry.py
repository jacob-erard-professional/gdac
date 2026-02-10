from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import yaml


@dataclass(frozen=True)
class ColumnDefinition:
    name: str
    dtype: str
    required: bool
    classification: str
    description: str


@dataclass(frozen=True)
class ColumnRegistry:
    version: str
    columns: List[ColumnDefinition]
    hash: str

    @property
    def column_names(self) -> List[str]:
        return [c.name for c in self.columns]

    @property
    def required_columns(self) -> List[str]:
        return [c.name for c in self.columns if c.required]

    def validate_input_columns(self, input_columns: List[str]) -> Dict[str, List[str]]:
        missing = [c for c in self.required_columns if c not in input_columns]
        unknown = [c for c in input_columns if c not in self.column_names]
        return {"missing": missing, "unknown": unknown}


def load_column_registry(path: Path) -> ColumnRegistry:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    columns = [
        ColumnDefinition(
            name=item["name"],
            dtype=item.get("dtype", "string"),
            required=bool(item.get("required", False)),
            classification=item.get("classification", "pass_through"),
            description=item.get("description", ""),
        )
        for item in data.get("columns", [])
    ]
    normalized = {
        "version": data.get("version", "0.0.0"),
        "columns": [c.__dict__ for c in columns],
    }
    registry_hash = hashlib.sha256(
        json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return ColumnRegistry(version=normalized["version"], columns=columns, hash=registry_hash)
