from __future__ import annotations

import pandas as pd


def preserve_original_brand(df: pd.DataFrame) -> pd.DataFrame:
    if "brand_original" not in df.columns:
        df = df.copy()
        df["brand_original"] = df["brand"]
    return df
