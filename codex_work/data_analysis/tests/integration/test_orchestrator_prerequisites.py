"""Tests for test orchestrator prerequisites behavior."""

from pathlib import Path
from src.pipeline.config import RunRequest
from src.pipeline.orchestrator import run_pipeline


def test_full_pipeline_stage_ordering(tmp_path: Path):
    raw = tmp_path / 'data' / 'raw' / '2024'
    raw.mkdir(parents=True, exist_ok=True)
    (raw / 'tweets.csv').write_text('tweet_id,created_at,text,user_id\n1,2024-02-11 10:00:00,ok,u1\n', encoding='utf-8')
    req = RunRequest(mode='full_year', stage=None, year='2024', data_dir=None)
    res = run_pipeline(tmp_path, req)[0]
    assert [s['stage'] for s in res.stages] == ['ingest', 'clean', 'process', 'analyze']
