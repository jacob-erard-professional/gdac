import csv
from pathlib import Path
from src.pipeline.config import RunRequest
from src.pipeline.orchestrator import run_pipeline


def test_clean_stage_includes_expected_columns(tmp_path: Path):
    raw = tmp_path / 'data' / 'raw' / '2024'
    raw.mkdir(parents=True, exist_ok=True)
    (raw / 'tweets.csv').write_text(
        (
            'id,author_id,created_at,conversation_id,text,lang,possibly_sensitive,'
            'entities.hashtags,entities.urls,referenced_tweets,in_reply_to_user_id,'
            'public_metrics.retweet_count,public_metrics.reply_count,public_metrics.like_count,'
            'public_metrics.quote_count,public_metrics.bookmark_count,username,name\n'
            '1,42,2024-02-11 10:00:00,11,hello,en,false,#sb,,,99,3,2,1,0,0,tester,Test User\n'
        ),
        encoding='utf-8',
    )
    req = RunRequest(mode='full_year', stage=None, year='2024', data_dir=None)
    run_pipeline(tmp_path, req)

    with (tmp_path / 'data' / 'processed' / '2024' / 'cleaned.csv').open(newline='', encoding='utf-8') as f:
        header = csv.DictReader(f).fieldnames or []

    expected = [
        'id',
        'author_id',
        'created_at',
        'conversation_id',
        'text',
        'lang',
        'possibly_sensitive',
        'entities.hashtags',
        'entities.urls',
        'referenced_tweets',
        'in_reply_to_user_id',
        'public_metrics.retweet_count',
        'public_metrics.reply_count',
        'public_metrics.like_count',
        'public_metrics.quote_count',
        'public_metrics.bookmark_count',
        'username',
        'name',
    ]
    for column in expected:
        assert column in header
