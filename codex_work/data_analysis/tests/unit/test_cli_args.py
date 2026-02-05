from typer.testing import CliRunner
from src.cli.main import app

runner = CliRunner()


def test_requires_exactly_one_year_or_data_dir():
    r = runner.invoke(app, ['run', '--stage', 'clean'])
    assert r.exit_code != 0


def test_requires_stage_or_all():
    r = runner.invoke(app, ['run', '--year', '2024'])
    assert r.exit_code != 0


def test_all_mode_supports_all_years_without_year_or_data_dir(monkeypatch):
    calls = []

    def fake_run_pipeline(_base_dir, req):
        calls.append(req)
        return []

    monkeypatch.setattr('src.cli.run.run_pipeline', fake_run_pipeline)
    r = runner.invoke(app, ['run', '--all'])
    assert r.exit_code == 0
    assert calls and calls[0].mode == 'full_all_years'


def test_stage_mode_requires_year_or_data_dir():
    r = runner.invoke(app, ['run', '--stage', 'clean'])
    assert r.exit_code != 0
    assert 'Stage mode requires exactly one of --year or --data-dir' in r.stdout


def test_with_sentiment_requires_all_mode():
    r = runner.invoke(app, ['run', '--year', '2024', '--stage', 'clean', '--with-sentiment'])
    assert r.exit_code != 0
    assert 'are supported only with --all' in r.stdout


def test_with_ad_sentiment_requires_with_sentiment():
    r = runner.invoke(app, ['run', '--year', '2024', '--all', '--with-ad-sentiment'])
    assert r.exit_code != 0
    assert '--with-ad-sentiment requires --with-sentiment' in r.stdout


def test_with_deep_sentiment_requires_all_mode():
    r = runner.invoke(app, ['run', '--year', '2024', '--stage', 'clean', '--with-deep-sentiment'])
    assert r.exit_code != 0
    assert 'are supported only with --all' in r.stdout
