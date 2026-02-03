import pytest
from typer.testing import CliRunner
from src.cli.main import app

runner = CliRunner()


def test_requires_exactly_one_year_or_data_dir():
    r = runner.invoke(app, ['run', '--stage', 'clean'])
    assert r.exit_code != 0


def test_requires_stage_or_all():
    r = runner.invoke(app, ['run', '--year', '2024'])
    assert r.exit_code != 0
