from pathlib import Path
import typer
from src.pipeline.config import RunRequest
from src.pipeline.orchestrator import run_pipeline


def run_command(
    year: str = typer.Option(None, "--year"),
    data_dir: Path = typer.Option(None, "--data-dir"),
    stage: str = typer.Option(None, "--stage"),
    all_: bool = typer.Option(False, "--all"),
    with_sentiment: bool = typer.Option(False, "--with-sentiment"),
    sentiment_dry_run: bool = typer.Option(False, "--sentiment-dry-run"),
    sentiment_verbose: bool = typer.Option(False, "--sentiment-verbose"),
):
    if bool(stage) == bool(all_):
        raise typer.BadParameter("Provide exactly one of --stage or --all")

    base_dir = Path(__file__).resolve().parents[2]
    resolved_data_dir = data_dir
    if resolved_data_dir and not resolved_data_dir.is_absolute():
        resolved_data_dir = (base_dir / resolved_data_dir).resolve()

    if stage:
        if with_sentiment:
            raise typer.BadParameter("--with-sentiment is supported only with --all")
        if bool(year) == bool(resolved_data_dir):
            raise typer.BadParameter("Stage mode requires exactly one of --year or --data-dir")
        mode = 'stage'
    else:
        if year and resolved_data_dir:
            raise typer.BadParameter("Provide only one of --year or --data-dir with --all")
        mode = 'full_all_years' if not year and not resolved_data_dir else 'full_year'

    req = RunRequest(
        mode=mode,
        stage=stage,
        year=year,
        data_dir=resolved_data_dir,
        deterministic=True,
        with_sentiment=with_sentiment,
        sentiment_dry_run=sentiment_dry_run,
        sentiment_verbose=sentiment_verbose,
    )
    results = run_pipeline(base_dir, req)
    for result in results:
        typer.echo(f"year={result.year} mode={result.mode} status={result.status} stages={len(result.stages)}")
