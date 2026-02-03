from pathlib import Path
from src.pipeline.config import RunRequest
from src.pipeline.orchestrator import run_pipeline


def test_quickstart_smoke(tmp_path: Path):
    raw = tmp_path / 'data' / 'raw' / '2024'
    raw.mkdir(parents=True, exist_ok=True)
    (raw / 'tweets.csv').write_text('tweet_id,created_at,text,user_id\n1,2024-02-11 10:00:00,#sb great,u1\n', encoding='utf-8')
    req = RunRequest(mode='full_year', stage=None, year='2024', data_dir=None)
    result = run_pipeline(tmp_path, req)[0]
    assert result.status == 'success'
