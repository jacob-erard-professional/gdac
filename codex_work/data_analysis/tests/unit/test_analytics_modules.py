from pathlib import Path
from src.analytics.registry import module_registry


def test_modules_produce_files(tmp_path: Path):
    rows = [{'brand_tag': 'b', 'sentiment_label': 'neutral', 'hashtags': 'a|b', 'retweet_count': '1', 'favorite_count': '2', 'game_phase': 'q1'}]
    for name, fn in module_registry().items():
        out = fn(rows, '2024', tmp_path)
        assert out.exists(), name
