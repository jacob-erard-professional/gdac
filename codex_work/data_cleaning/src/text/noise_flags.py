from __future__ import annotations

import pandas as pd


RETWEET_PREFIX = "RT "


def add_noise_flags(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["is_retweet"] = df["text"].map(lambda v: isinstance(v, str) and v.startswith(RETWEET_PREFIX))
    seen = set()

    def mark_duplicate(text: str) -> bool:
        key = text
        if key in seen:
            return True
        seen.add(key)
        return False

    df["is_duplicate"] = df["text_normalized"].map(mark_duplicate)
    return df
