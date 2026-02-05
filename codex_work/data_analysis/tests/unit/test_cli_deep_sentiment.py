from pathlib import Path

from typer.testing import CliRunner

from src.cli.main import app

runner = CliRunner()


def test_deep_sentiment_requires_year_with_input_file(tmp_path: Path):
    data = tmp_path / "data.csv"
    data.write_text("tweet_id,text,year\n1,hello,2024\n", encoding="utf-8")

    result = runner.invoke(app, ["deep-sentiment", "--input-file", str(data)])

    assert result.exit_code != 0
    assert "--year is required when using --input-file" in result.stdout


def test_deep_sentiment_runs_dry_run(monkeypatch, tmp_path: Path):
    cleaned = tmp_path / "custom.csv"
    cleaned.write_text("tweet_id,text,year\n1,hello,2024\n", encoding="utf-8")

    def fake_run_deep_sentiment(**kwargs):
        manifest = type(
            "Manifest",
            (),
            {
                "record_counts": {"input": 1, "output": 0},
                "notes": ["dry_run=true"],
            },
        )()
        return None, manifest

    monkeypatch.setattr("src.cli.deep_sentiment.run_deep_sentiment", fake_run_deep_sentiment)

    result = runner.invoke(
        app,
        ["deep-sentiment", "--input-file", str(cleaned), "--year", "2024", "--dry-run"],
    )

    assert result.exit_code == 0
    assert "deep sentiment dry-run completed" in result.stdout


def test_deep_sentiment_surfaces_model_mapping_errors(monkeypatch, tmp_path: Path):
    cleaned = tmp_path / "custom.csv"
    cleaned.write_text("tweet_id,text,year\n1,hello,2024\n", encoding="utf-8")

    def fake_run_deep_sentiment(**kwargs):
        raise ValueError("Unable to map model label 'mystery' to required taxonomy")

    monkeypatch.setattr("src.cli.deep_sentiment.run_deep_sentiment", fake_run_deep_sentiment)

    result = runner.invoke(
        app,
        ["deep-sentiment", "--input-file", str(cleaned), "--year", "2024"],
    )

    assert result.exit_code != 0
    assert isinstance(result.exception, ValueError)
    assert "Unable to map model label" in str(result.exception)
