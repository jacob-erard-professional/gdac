from pathlib import Path
from src.pipeline.config import RunRequest
from src.pipeline.orchestrator import run_pipeline
from src.pipeline import orchestrator
from src.utils.checksums import sha256_file


def _seed(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    (path / 'tweets.csv').write_text(
        'tweet_id,created_at,text,user_id\n1,2024-02-11 10:00:00,Great #Ad @acme,a\n',
        encoding='utf-8',
    )


def test_rerun_is_deterministic(tmp_path: Path):
    _seed(tmp_path / 'data' / 'raw' / '2024')
    req = RunRequest(mode='full_year', stage=None, year='2024', data_dir=None)
    run_pipeline(tmp_path, req)
    out = tmp_path / 'outputs' / 'analytics' / '2024' / 'hashtags_frequency.json'
    c1 = sha256_file(out)
    run_pipeline(tmp_path, req)
    c2 = sha256_file(out)
    assert c1 == c2


def test_rerun_is_deterministic_with_deep_sentiment(monkeypatch, tmp_path: Path):
    _seed(tmp_path / 'data' / 'raw' / '2024')

    def fake_deep_sentiment_run(config, **kwargs):
        out = tmp_path / 'sentiment' / 'deep' / config.year / 'deep_sentiment.json'
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            '{"metadata":{"model_id":"fake"},"records":[{"tweet_id":"1","hashtags":["ad"],"text":"Great #Ad @acme","main_sentiment":"joy"}]}',
            encoding='utf-8',
        )
        return type('Manifest', (), {
            'input_files': [str(config.processed_dir / 'cleaned.csv')],
            'output_files': [str(out)],
            'record_counts': {'input': 1, 'output': 1},
            'started_at': '',
            'completed_at': '',
            'notes': ['model_id=fake'],
        })()

    monkeypatch.setitem(orchestrator.RUNNERS, 'deep_sentiment', fake_deep_sentiment_run)

    req = RunRequest(mode='full_year', stage=None, year='2024', data_dir=None, with_deep_sentiment=True)
    run_pipeline(tmp_path, req)
    out = tmp_path / 'sentiment' / 'deep' / '2024' / 'deep_sentiment.json'
    c1 = sha256_file(out)
    run_pipeline(tmp_path, req)
    c2 = sha256_file(out)
    assert c1 == c2
