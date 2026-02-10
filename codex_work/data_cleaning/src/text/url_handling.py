from __future__ import annotations

import re
from typing import Literal

import pandas as pd


URL_PATTERN = re.compile(r"https?://\S+")


def handle_urls(text: str, mode: Literal["remove", "replace"], token: str = "[URL]") -> str:
    if mode == "remove":
        return URL_PATTERN.sub("", text).strip()
    if mode == "replace":
        return URL_PATTERN.sub(token, text).strip()
    raise ValueError("Unknown URL handling mode")


def apply_url_handling(df: pd.DataFrame, mode: Literal["remove", "replace"], token: str = "[URL]") -> pd.DataFrame:
    df = df.copy()
    df["text_normalized"] = df["text_normalized"].map(lambda v: handle_urls(v, mode, token))
    df["url_handling_applied"] = True
    return df
