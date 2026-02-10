from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd


def quarantine_rows(df: pd.DataFrame, invalid_mask: pd.Series, reasons: Dict[str, int], output_dir: Path) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    quarantine_path = output_dir / "quarantine.csv"
    quarantined = df[~invalid_mask].copy()
    if reasons:
        reason = ";".join(sorted(reasons.keys()))
        quarantined["quarantine_reason"] = reason
    quarantined.to_csv(quarantine_path, index=False)
    return quarantine_path
