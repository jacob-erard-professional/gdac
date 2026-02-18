"""Tests for test full all years mode behavior."""

from pathlib import Path
from src.pipeline.config import RunRequest
from src.pipeline.orchestrator import run_pipeline


def test_full_all_years(tmp_path: Path):
    for y in ('2023', '2024'):
        raw = tmp_path / 'data' / 'raw' / y
        raw.mkdir(parents=True, exist_ok=True)
        (raw / 'tweets.csv').write_text('tweet_id,created_at,text,user_id\n1,2024-02-11 10:00:00,ok,u1\n', encoding='utf-8')
    req = RunRequest(mode='full_all_years', stage=None, year=None, data_dir=None)
    results = run_pipeline(tmp_path, req)
    assert len(results) == 2
