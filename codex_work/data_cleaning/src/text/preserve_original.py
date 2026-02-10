from __future__ import annotations

import pandas as pd


def preserve_original_text(df: pd.DataFrame) -> pd.DataFrame:
    if "text_original" not in df.columns:
        df = df.copy()
        df["text_original"] = df["text"]
    return df
