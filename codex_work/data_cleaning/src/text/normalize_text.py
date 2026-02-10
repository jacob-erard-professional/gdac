from __future__ import annotations

import re
import unicodedata
from typing import Literal

import pandas as pd


WhitespacePattern = re.compile(r"\s+")


def normalize_text_value(value: str, casing: Literal["none", "lower", "upper"]) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    normalized = WhitespacePattern.sub(" ", normalized).strip()
    if casing == "lower":
        normalized = normalized.lower()
    elif casing == "upper":
        normalized = normalized.upper()
    return normalized


def apply_text_normalization(df: pd.DataFrame, casing: Literal["none", "lower", "upper"]) -> pd.DataFrame:
    df = df.copy()
    df["text_normalized"] = df["text"].map(lambda v: normalize_text_value(v, casing))
    return df
