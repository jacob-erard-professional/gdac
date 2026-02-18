"""Tests for test with ad sentiment pipeline mode behavior."""

from pathlib import Path

from src.pipeline import orchestrator
from src.pipeline.config import RunRequest
from src.pipeline.orchestrator import run_pipeline


def test_full_year_with_ad_sentiment_runs_stage(monkeypatch, tmp_path: Path):
    raw = tmp_path / "data" / "raw" / "2024"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "tweets.csv").write_text(
        "tweet_id,created_at,text,user_id\n"
        "1,2024-02-11 10:00:00,#x great,u1\n",
        encoding="utf-8",
    )

    captured = {"sentiment": False, "ad_sentiment": False}

    def fake_sentiment_run(config, **kwargs):
        captured["sentiment"] = True
        sentiment_out = tmp_path / "sentiment" / "bertweet" / "2024"
        sentiment_out.mkdir(parents=True, exist_ok=True)
        (sentiment_out / "sentiment.json").write_text(
            '{"metadata":{},"records":[]}',
            encoding="utf-8",
        )
        return type("Manifest", (), {
            "input_files": [str(config.processed_dir / "cleaned.csv")],
            "output_files": [str(sentiment_out / "sentiment.json")],
            "record_counts": {"input": 1, "output": 0},
            "started_at": "",
            "completed_at": "",
            "notes": [],
        })()

    def fake_ad_sentiment_run(config, **kwargs):
        captured["ad_sentiment"] = True
        return type("Manifest", (), {
            "input_files": [str(tmp_path / "sentiment" / "bertweet" / "2024" / "sentiment.json")],
            "output_files": [],
            "record_counts": {"input": 0, "output": 0},
            "started_at": "",
            "completed_at": "",
            "notes": [],
        })()

    monkeypatch.setitem(orchestrator.RUNNERS, "sentiment", fake_sentiment_run)
    monkeypatch.setitem(orchestrator.RUNNERS, "ad_sentiment", fake_ad_sentiment_run)

    req = RunRequest(
        mode="full_year",
        stage=None,
        year="2024",
        data_dir=None,
        with_sentiment=True,
        with_ad_sentiment=True,
        sentiment_dry_run=True,
    )
    result = run_pipeline(tmp_path, req)[0]

    assert captured["sentiment"] is True
    assert captured["ad_sentiment"] is True
    stage_names = [s["stage"] for s in result.stages]
    assert "sentiment" in stage_names
    assert "ad_sentiment" in stage_names
