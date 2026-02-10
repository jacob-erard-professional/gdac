from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
import yaml


def load_alias_map(path: Path) -> Dict[str, str]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    aliases = data.get("aliases", {})
    mapping: Dict[str, str] = {}
    for canonical, values in aliases.items():
        canonical_norm = canonical.strip().lower()
        mapping[canonical_norm] = canonical_norm
        for alias in values:
            mapping[alias.strip().lower()] = canonical_norm
    return mapping


def normalize_brand_value(value: str, alias_map: Dict[str, str]) -> Tuple[str, bool, bool]:
    normalized = value.strip().lower()
    if normalized in alias_map:
        canonical = alias_map[normalized]
        return canonical, canonical != normalized, True
    return normalized, False, False


def apply_brand_normalization(df: pd.DataFrame, alias_config_path: Path) -> pd.DataFrame:
    df = df.copy()
    alias_map = load_alias_map(alias_config_path)
    results = df["brand"].map(lambda v: normalize_brand_value(v, alias_map))
    df["brand_normalized"] = results.map(lambda v: v[0])
    df["alias_resolved"] = results.map(lambda v: v[1])
    df["brand_known"] = results.map(lambda v: v[2])
    return df
