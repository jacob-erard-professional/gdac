"""Tests for test cli run everything behavior."""

from pathlib import Path

from typer.testing import CliRunner

from src.cli.main import app

runner = CliRunner()


class _Cfg:
    def __init__(self, year: str, analytics_dir: Path):
        self.year = year
        self.analytics_dir = analytics_dir


def test_run_everything_rejects_unknown_exclude():
    result = runner.invoke(app, ["run-everything", "--data-dir", "data/raw/2024", "--exclude", "nope"])
    assert result.exit_code != 0
    assert "Unknown --exclude value" in result.stdout


def test_run_everything_requires_sentiment_for_ad_sentiment():
    result = runner.invoke(
        app,
        ["run-everything", "--data-dir", "data/raw/2024", "--exclude", "sentiment"],
    )
    assert result.exit_code != 0
    assert "ad-sentiment requires sentiment" in result.stdout


def test_run_everything_requires_data_dir():
    result = runner.invoke(app, ["run-everything", "--exclude", "group-brands"])
    assert result.exit_code != 0
    assert "requires --data-dir" in result.stdout


def test_run_everything_rejects_year_flag():
    result = runner.invoke(app, ["run-everything", "--year", "2024", "--data-dir", "data/raw/2024"])
    assert result.exit_code != 0
    assert "no longer accepts --year" in result.stdout


def test_run_everything_runs_pipeline_and_group_brands(monkeypatch, tmp_path: Path):
    analytics_dir = tmp_path / "outputs" / "analytics" / "2024"
    analytics_dir.mkdir(parents=True, exist_ok=True)
    (analytics_dir / "hashtags_frequency.json").write_text('{"year":"2024","hashtags":[]}', encoding="utf-8")

    calls = {}

    def fake_resolve(_base, year=None, data_dir=None):
        assert year is None
        assert data_dir is not None
        return _Cfg("2024", analytics_dir)

    def fake_pipeline(_base, req):
        calls["req"] = req
        return [type("R", (), {"year": "2024", "mode": "full_year", "status": "success"})()]

    def fake_brand_grouping(**kwargs):
        calls["brand"] = kwargs
        (analytics_dir / "brand_groups.json").write_text('{"year":"2024","brands":[]}', encoding="utf-8")
        return analytics_dir / "brand_groups.json"

    monkeypatch.setattr("src.cli.run_everything.resolve_year_config", fake_resolve)
    monkeypatch.setattr("src.cli.run_everything.run_pipeline", fake_pipeline)
    monkeypatch.setattr("src.agents.brand_grouping_agent.run_brand_grouping", fake_brand_grouping)

    result = runner.invoke(
        app,
        [
            "run-everything",
            "--data-dir",
            str(tmp_path / "data" / "raw" / "2024"),
            "--grouping-model",
            "openai/gpt-4.1",
            "--exclude",
            "group-parent-companies",
        ],
    )

    assert result.exit_code == 0
    assert calls["req"].with_sentiment is True
    assert calls["req"].with_ad_sentiment is True
    assert calls["brand"]["hashtags_path"] == analytics_dir / "hashtags_frequency.json"


def test_run_everything_defaults_agentic_emotion_model_to_grouping_model(monkeypatch, tmp_path: Path):
    analytics_dir = tmp_path / "outputs" / "analytics" / "2024"
    analytics_dir.mkdir(parents=True, exist_ok=True)

    calls = {}

    def fake_resolve(_base, year=None, data_dir=None):
        assert year is None
        assert data_dir is not None
        return _Cfg("2024", analytics_dir)

    def fake_pipeline(_base, req):
        calls["req"] = req
        return [type("R", (), {"year": "2024", "mode": "full_year", "status": "success"})()]

    monkeypatch.setattr("src.cli.run_everything.resolve_year_config", fake_resolve)
    monkeypatch.setattr("src.cli.run_everything.run_pipeline", fake_pipeline)

    result = runner.invoke(
        app,
        [
            "run-everything",
            "--data-dir",
            str(tmp_path / "data" / "raw" / "2024"),
            "--grouping-model",
            "openai/gpt-4.1",
            "--exclude",
            "group-brands",
            "--exclude",
            "group-parent-companies",
            "--exclude",
            "sentiment-maps",
            "--exclude",
            "emotion-breakdowns",
        ],
    )

    assert result.exit_code == 0
    assert calls["req"].with_agentic_emotion is True
    assert calls["req"].agentic_emotion_model == "openai/gpt-4.1"
