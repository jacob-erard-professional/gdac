from pathlib import Path

from typer.testing import CliRunner

from src.cli.main import app

runner = CliRunner()


def test_parent_company_sentiment_requires_year_or_data_dir():
    result = runner.invoke(app, ["parent-company-sentiment"])
    assert result.exit_code != 0


def test_parent_company_sentiment_runs(monkeypatch, tmp_path: Path):
    captured = {}

    class Outputs:
        joined_parquet = tmp_path / "joined.parquet"
        summary_json = tmp_path / "summary.json"
        summary_csv = tmp_path / "summary.csv"

    class Manifest:
        record_counts = {"input": 1, "output": 1}

    def fake_run(**kwargs):
        captured.update(kwargs)
        return Outputs(), Manifest()

    monkeypatch.setattr("src.cli.parent_company_sentiment.run_parent_company_sentiment_analysis", fake_run)

    result = runner.invoke(app, ["parent-company-sentiment", "--year", "2024"])

    assert result.exit_code == 0
    assert captured["year"] == 2024
