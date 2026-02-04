from pathlib import Path

from src.pipeline.config import RunRequest
from src.pipeline import orchestrator
from src.pipeline.orchestrator import run_pipeline


def test_full_year_with_sentiment_runs_sentiment_stage(monkeypatch, tmp_path: Path):
    raw = tmp_path / "data" / "raw" / "2024"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "tweets.csv").write_text(
        "tweet_id,created_at,text,user_id\n"
        "1,2024-02-11 10:00:00,#x great,u1\n",
        encoding="utf-8",
    )

    captured = {"called": False}

    def fake_sentiment_run(config, **kwargs):
        captured["called"] = True
        captured["kwargs"] = kwargs
        return type("Manifest", (), {
            "input_files": [str(config.processed_dir / "cleaned.csv")],
            "output_files": [],
            "record_counts": {"input": 1, "output": 0},
            "started_at": "",
            "completed_at": "",
            "notes": ["dry_run=true"],
        })()

    monkeypatch.setitem(orchestrator.RUNNERS, "sentiment", fake_sentiment_run)

    req = RunRequest(
        mode="full_year",
        stage=None,
        year="2024",
        data_dir=None,
        with_sentiment=True,
        sentiment_dry_run=True,
    )
    result = run_pipeline(tmp_path, req)[0]

    assert captured["called"] is True
    stage_names = [s["stage"] for s in result.stages]
    assert "sentiment" in stage_names
    assert captured["kwargs"]["dry_run"] is True
