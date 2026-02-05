from pathlib import Path

from src.pipeline import orchestrator
from src.pipeline.config import RunRequest
from src.pipeline.orchestrator import run_pipeline


def _seed_year(raw_root: Path, year: str, text: str):
    year_dir = raw_root / year
    year_dir.mkdir(parents=True, exist_ok=True)
    (year_dir / "tweets.csv").write_text(
        "tweet_id,created_at,text,user_id\n"
        f"1,2024-02-11 10:00:00,{text},u1\n",
        encoding="utf-8",
    )


def test_full_year_with_deep_sentiment_runs_stage(monkeypatch, tmp_path: Path):
    _seed_year(tmp_path / "data" / "raw", "2024", "#x great")

    captured = {"deep_sentiment": False}

    def fake_deep_sentiment_run(config, **kwargs):
        captured["deep_sentiment"] = True
        captured["kwargs"] = kwargs
        return type(
            "Manifest",
            (),
            {
                "input_files": [str(config.processed_dir / "cleaned.csv")],
                "output_files": [],
                "record_counts": {"input": 1, "output": 0},
                "started_at": "",
                "completed_at": "",
                "notes": [],
            },
        )()

    monkeypatch.setitem(orchestrator.RUNNERS, "deep_sentiment", fake_deep_sentiment_run)

    req = RunRequest(
        mode="full_year",
        stage=None,
        year="2024",
        data_dir=None,
        with_deep_sentiment=True,
        deep_sentiment_dry_run=True,
    )
    result = run_pipeline(tmp_path, req)[0]

    assert captured["deep_sentiment"] is True
    stage_names = [s["stage"] for s in result.stages]
    assert "deep_sentiment" in stage_names
    assert captured["kwargs"]["dry_run"] is True


def test_full_all_years_with_deep_sentiment_runs_each_year(monkeypatch, tmp_path: Path):
    raw_root = tmp_path / "data" / "raw"
    _seed_year(raw_root, "2023", "#a one")
    _seed_year(raw_root, "2024", "#b two")

    called_years = []

    def fake_deep_sentiment_run(config, **kwargs):
        called_years.append(config.year)
        return type(
            "Manifest",
            (),
            {
                "input_files": [str(config.processed_dir / "cleaned.csv")],
                "output_files": [],
                "record_counts": {"input": 1, "output": 0},
                "started_at": "",
                "completed_at": "",
                "notes": [],
            },
        )()

    monkeypatch.setitem(orchestrator.RUNNERS, "deep_sentiment", fake_deep_sentiment_run)

    req = RunRequest(
        mode="full_all_years",
        stage=None,
        year=None,
        data_dir=None,
        with_deep_sentiment=True,
        deep_sentiment_dry_run=True,
    )
    run_pipeline(tmp_path, req)

    assert sorted(called_years) == ["2023", "2024"]
