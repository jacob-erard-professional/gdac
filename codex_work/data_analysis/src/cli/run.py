from pathlib import Path
import typer
from src.pipeline.config import RunRequest
from src.pipeline.orchestrator import run_pipeline


def run_command(
    year: str = typer.Option(None, "--year"),
    data_dir: Path = typer.Option(None, "--data-dir"),
    stage: str = typer.Option(None, "--stage"),
    all_: bool = typer.Option(False, "--all"),
):
    if bool(year) == bool(data_dir):
        raise typer.BadParameter("Provide exactly one of --year or --data-dir")
    if bool(stage) == bool(all_):
        raise typer.BadParameter("Provide exactly one of --stage or --all")

    mode = 'stage' if stage else 'full_year'
    if all_ and not stage and not year and data_dir:
        mode = 'full_year'
    req = RunRequest(mode=mode, stage=stage, year=year, data_dir=data_dir, deterministic=True)
    base_dir = Path(__file__).resolve().parents[2]
    results = run_pipeline(base_dir, req)
    for result in results:
        typer.echo(f"year={result.year} mode={result.mode} status={result.status} stages={len(result.stages)}")
