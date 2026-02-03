from __future__ import annotations

from pathlib import Path

import pytest

from src.pipeline.data_locator import DataResolutionError, resolve_event_year_input


def test_resolve_event_year_input_default_file(tmp_path: Path):
    csv_path = tmp_path / "superbowl" / "2024" / "file.csv"
    csv_path.parent.mkdir(parents=True)
    csv_path.write_text("id,text\n1,test\n")

    resolved = resolve_event_year_input("superbowl", 2024, data_root=str(tmp_path))
    assert resolved == str(csv_path)


def test_resolve_event_year_input_missing_raises(tmp_path: Path):
    with pytest.raises(DataResolutionError):
        resolve_event_year_input("superbowl", 2025, data_root=str(tmp_path))
