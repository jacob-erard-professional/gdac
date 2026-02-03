from pathlib import Path
from src.utils.guards import ensure_not_raw_output
import pytest


def test_disallow_raw_writes():
    with pytest.raises(ValueError):
        ensure_not_raw_output(Path('/x/data/raw/2024/out.csv'))
