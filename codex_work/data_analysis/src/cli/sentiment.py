from pathlib import Path

import typer

from src.agents.sentiment.config import AgentModelConfig, RuntimeConfig
from src.agents.sentiment.orchestrator import run_sentiment_for_config
from src.pipeline.path_resolution import resolve_year_config


def sentiment_command(
    year: str = typer.Option(None, "--year"),
    data_dir: Path = typer.Option(None, "--data-dir"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    verbose: bool = typer.Option(False, "--verbose"),
):
    if bool(year) == bool(data_dir):
        raise typer.BadParameter("Provide exactly one of --year or --data-dir")

    base_dir = Path(__file__).resolve().parents[2]
    resolved_data_dir = data_dir
    if resolved_data_dir and not resolved_data_dir.is_absolute():
        resolved_data_dir = (base_dir / resolved_data_dir).resolve()

    cfg = resolve_year_config(base_dir, year=year, data_dir=resolved_data_dir)
    cleaned = cfg.processed_dir / "cleaned.csv"
    if not cleaned.exists():
        raise typer.BadParameter(f"Missing required input file: {cleaned}")

    records_path, summary_path, _manifest = run_sentiment_for_config(
        year=cfg.year,
        cleaned_csv=cleaned,
        analytics_dir=cfg.analytics_dir,
        model_cfg=AgentModelConfig(),
        runtime_cfg=RuntimeConfig(dry_run=dry_run, verbose=verbose),
    )
    typer.echo(f"sentiment records written to {records_path}")
    typer.echo(f"sentiment summary written to {summary_path}")

