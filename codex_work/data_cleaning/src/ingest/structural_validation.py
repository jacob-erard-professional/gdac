from __future__ import annotations

from typing import Dict, List, Tuple

import pandas as pd


def validate_required_columns(df: pd.DataFrame, required_columns: List[str]) -> Tuple[pd.Series, Dict[str, int]]:
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        reasons = {"missing_columns": len(df)}
        return pd.Series([False] * len(df)), reasons
    return pd.Series([True] * len(df)), {}


def validate_types(df: pd.DataFrame, required_columns: List[str]) -> Tuple[pd.Series, Dict[str, int]]:
    # With dtype=str ingestion, type validation is limited to presence of string values.
    invalid = pd.Series([False] * len(df))
    for col in required_columns:
        invalid = invalid | df[col].map(lambda v: not isinstance(v, str))
    reasons = {"invalid_type": int(invalid.sum())} if invalid.any() else {}
    return ~invalid, reasons
