from pathlib import Path
from src.pipeline.config import RunRequest
from src.pipeline.orchestrator import run_pipeline
from src.utils.checksums import sha256_file


def _seed(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    (path / 'tweets.csv').write_text('tweet_id,created_at,text,user_id\n1,2024-02-11 10:00:00,Great #Ad,a\n', encoding='utf-8')


def test_rerun_is_deterministic(tmp_path: Path):
    _seed(tmp_path / 'data' / 'raw' / '2024')
    req = RunRequest(mode='full_year', stage=None, year='2024', data_dir=None)
    run_pipeline(tmp_path, req)
    out = tmp_path / 'data' / 'analytics' / '2024' / 'sentiment_metrics.json'
    c1 = sha256_file(out)
    run_pipeline(tmp_path, req)
    c2 = sha256_file(out)
    assert c1 == c2
