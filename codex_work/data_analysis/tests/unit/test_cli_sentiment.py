"""Tests for test cli sentiment behavior."""

from pathlib import Path

from typer.testing import CliRunner

from src.cli.main import app

runner = CliRunner()


def test_sentiment_requires_year_with_input_file(tmp_path: Path):
    data = tmp_path / "data.csv"
    data.write_text("tweet_id,text,year\n1,hello,2024\n", encoding="utf-8")

    result = runner.invoke(app, ["sentiment", "--input-file", str(data)])

    assert result.exit_code != 0
    assert "--year is required when using --input-file" in result.stdout


def test_sentiment_runs_dry_run(monkeypatch, tmp_path: Path):
    cleaned = tmp_path / "custom.csv"
    cleaned.write_text("tweet_id,text,year\n1,hello,2024\n", encoding="utf-8")

    def fake_run_sentiment(**kwargs):
        manifest = type("Manifest", (), {
            "record_counts": {"input": 1, "output": 0},
            "notes": ["dry_run=true"],
        })()
        return None, manifest

    monkeypatch.setattr("src.cli.sentiment.run_bertweet_sentiment", fake_run_sentiment)

    result = runner.invoke(
        app,
        ["sentiment", "--input-file", str(cleaned), "--year", "2024", "--dry-run"],
        env={},
    )

    assert result.exit_code == 0
    assert "sentiment dry-run completed" in result.stdout
