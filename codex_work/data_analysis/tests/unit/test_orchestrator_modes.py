from pathlib import Path
from src.pipeline.config import RunRequest
from src.pipeline.orchestrator import run_pipeline


def test_orchestrator_rejects_missing_stage(tmp_path: Path):
    req = RunRequest(mode='stage', stage=None, year='2024', data_dir=None)
    try:
        run_pipeline(tmp_path, req)
        assert False
    except ValueError:
        assert True


def test_full_year_honors_explicit_data_dir(tmp_path: Path):
    default_raw = tmp_path / 'data' / 'raw' / '2024'
    default_raw.mkdir(parents=True, exist_ok=True)
    (default_raw / 'tweets.csv').write_text(
        'tweet_id,created_at,text,user_id\n100,2024-02-11 10:00:00,default,u1\n',
        encoding='utf-8',
    )

    explicit_raw = tmp_path / 'fixtures' / '2024'
    explicit_raw.mkdir(parents=True, exist_ok=True)
    (explicit_raw / 'tweets.csv').write_text(
        'tweet_id,created_at,text,user_id\n999,2024-02-11 10:00:00,explicit,u9\n',
        encoding='utf-8',
    )

    req = RunRequest(mode='full_year', stage=None, year=None, data_dir=explicit_raw)
    run_pipeline(tmp_path, req)

    ingested = (tmp_path / 'data' / 'processed' / '2024' / 'ingested.csv').read_text(encoding='utf-8')
    assert '999' in ingested
    assert '100' not in ingested
