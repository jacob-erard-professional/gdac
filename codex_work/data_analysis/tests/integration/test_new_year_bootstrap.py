from pathlib import Path
from src.pipeline.config import RunRequest
from src.pipeline.orchestrator import run_pipeline


def test_new_year_works_without_code_changes(tmp_path: Path):
    raw = tmp_path / 'data' / 'raw' / '2025'
    raw.mkdir(parents=True, exist_ok=True)
    (raw / 'tweets.csv').write_text('tweet_id,created_at,text,user_id\n1,2025-02-10 10:00:00,ok,u1\n', encoding='utf-8')
    req = RunRequest(mode='full_year', stage=None, year='2025', data_dir=None)
    run_pipeline(tmp_path, req)
    assert (tmp_path / 'outputs' / 'analytics' / '2025' / 'sentiment_metrics.json').exists()
