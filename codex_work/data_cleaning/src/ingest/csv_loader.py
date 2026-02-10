from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd


def load_csv_files(input_dir: Path) -> List[Tuple[Path, pd.DataFrame]]:
    input_dir = Path(input_dir)
    files = sorted(input_dir.glob("*.csv"))
    datasets: List[Tuple[Path, pd.DataFrame]] = []
    for path in files:
        df = pd.read_csv(
            path,
            dtype=str,
            keep_default_na=False,
            na_filter=False,
        )
        datasets.append((path, df))
    return datasets


def concatenate_datasets(datasets: List[Tuple[Path, pd.DataFrame]]) -> Tuple[List[Path], pd.DataFrame]:
    paths = [path for path, _ in datasets]
    if not datasets:
        return paths, pd.DataFrame()
    frames = [df for _, df in datasets]
    combined = pd.concat(frames, ignore_index=True)
    return paths, combined
