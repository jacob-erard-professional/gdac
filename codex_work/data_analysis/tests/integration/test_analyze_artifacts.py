from pathlib import Path
from src.pipeline.config import RunRequest
from src.pipeline.orchestrator import run_pipeline


def test_analyze_outputs_exist(tmp_path: Path):
    raw = tmp_path / 'data' / 'raw' / '2024'
    raw.mkdir(parents=True, exist_ok=True)
    (raw / 'tweets.csv').write_text('tweet_id,created_at,text,user_id\n1,2024-02-11 10:00:00,#x great,u1\n', encoding='utf-8')
    req = RunRequest(mode='full_year', stage=None, year='2024', data_dir=None)
    run_pipeline(tmp_path, req)
    adir = tmp_path / 'data' / 'analytics' / '2024'
    expected = [
        'volume_metrics.json', 'sentiment_metrics.json', 'time_bucket_metrics.json',
        'roi_proxy_metrics.json', 'relationship_metrics.json', 'event_alignment_metrics.json',
        'text_network_metrics.json'
    ]
    for name in expected:
        assert (adir / name).exists()
