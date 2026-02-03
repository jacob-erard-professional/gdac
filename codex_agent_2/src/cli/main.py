from __future__ import annotations

import json
from pathlib import Path

import typer

from src.artifacts.manifest_store import ManifestStore
from src.pipeline.data_locator import DataResolutionError, resolve_inputs
from src.pipeline.orchestrator import Orchestrator

app = typer.Typer(help="Modular NLP pipeline CLI")
stage_app = typer.Typer()
artifacts_app = typer.Typer()
manifest_app = typer.Typer()

app.add_typer(stage_app, name="stage")
app.add_typer(artifacts_app, name="artifacts")
artifacts_app.add_typer(manifest_app, name="manifest")


@stage_app.command("run")
def run_stage(
    stage_name: str,
    input: list[str] | None = typer.Option(None, "--input"),
    output: list[str] = typer.Option(..., "--output"),
    config: str = typer.Option(..., "--config"),
    event: str | None = typer.Option(None, "--event"),
    year: int | None = typer.Option(None, "--year"),
    file_name: str = typer.Option("file.csv", "--file-name"),
    data_root: str = typer.Option("data", "--data-root"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    manifest_path: str = typer.Option("artifacts/manifest.json", "--manifest-path"),
):
    try:
        resolved_inputs = resolve_inputs(input, event, year, data_root, file_name)
    except DataResolutionError as exc:
        raise typer.BadParameter(str(exc)) from exc
    orchestrator = Orchestrator(manifest_path)
    result = orchestrator.run_stage(
        stage_name,
        resolved_inputs,
        output,
        config,
        dry_run,
        event=event,
        year=year,
    )
    typer.echo(json.dumps(result, indent=2))


@stage_app.command("run-many")
def run_many(
    stages: str = typer.Option(..., "--stages"),
    input: list[str] | None = typer.Option(None, "--input"),
    output_root: str = typer.Option(..., "--output-root"),
    config: str = typer.Option(..., "--config"),
    event: str | None = typer.Option(None, "--event"),
    year: int | None = typer.Option(None, "--year"),
    file_name: str = typer.Option("file.csv", "--file-name"),
    data_root: str = typer.Option("data", "--data-root"),
    skip_completed: bool = typer.Option(False, "--skip-completed"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    manifest_path: str = typer.Option("artifacts/manifest.json", "--manifest-path"),
):
    stage_list = [s.strip() for s in stages.split(",") if s.strip()]
    try:
        resolved_inputs = resolve_inputs(input, event, year, data_root, file_name)
    except DataResolutionError as exc:
        raise typer.BadParameter(str(exc)) from exc
    orchestrator = Orchestrator(manifest_path)
    result = orchestrator.run_many(
        stage_list,
        resolved_inputs,
        output_root,
        config,
        skip_completed,
        dry_run,
        event=event,
        year=year,
    )
    typer.echo(json.dumps(result, indent=2))


@manifest_app.command("show")
def show_manifest(path: str = typer.Option(..., "--path")):
    manifest = ManifestStore(path).dump()
    typer.echo(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    app()
