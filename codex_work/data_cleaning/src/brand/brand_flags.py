from __future__ import annotations

import pandas as pd


def add_brand_flags(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["brand_empty"] = df["brand"].map(lambda v: isinstance(v, str) and v.strip() == "")
    df["brand_unknown"] = ~df.get("brand_known", False)
    df["brand_alias_resolved"] = df.get("alias_resolved", False)
    return df
