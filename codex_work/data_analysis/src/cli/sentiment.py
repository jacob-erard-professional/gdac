"""CLI entrypoints for sentiment workflows."""

from pathlib import Path

import typer

from src.pipeline.config import extract_base_year
from src.pipeline.path_resolution import resolve_year_config
from src.sentiment.bertweet import DEFAULT_MODEL_ID, run_bertweet_sentiment


def sentiment_command(
    year: str = typer.Option(None, "--year", help="Year for partitioning output and default input resolution"),
    data_dir: Path = typer.Option(None, "--data-dir", help="Raw year directory used to resolve year"),
    input_file: Path = typer.Option(None, "--input-file", help="Explicit CSV or Parquet input path"),
    model: str = typer.Option(DEFAULT_MODEL_ID, "--model", help="Hugging Face model identifier"),
    batch_size: int = typer.Option(64, "--batch-size", min=1),
    dry_run: bool = typer.Option(False, "--dry-run"),
    allow_fallback: bool = typer.Option(
        False,
        "--allow-fallback",
        help="Allow explicit fallback model if the default fails to load.",
    ),
    device: str = typer.Option("cuda", "--device", help="Inference device (cuda or cpu)"),
):
    supplied = [bool(year), bool(data_dir), bool(input_file)]
    if sum(supplied) == 0:
        raise typer.BadParameter("Provide one of --year, --data-dir, or --input-file")
    if input_file and data_dir:
        raise typer.BadParameter("--input-file cannot be combined with --data-dir")

    base_dir = Path(__file__).resolve().parents[2]

    if input_file:
        resolved_input = input_file if input_file.is_absolute() else (base_dir / input_file).resolve()
        if not resolved_input.exists():
            raise typer.BadParameter(f"Input file not found: {resolved_input}")
        if not year:
            raise typer.BadParameter("--year is required when using --input-file")
        target_year = int(year)
    else:
        if bool(year) == bool(data_dir):
            raise typer.BadParameter("Provide exactly one of --year or --data-dir")
        resolved_data_dir = data_dir
        if resolved_data_dir and not resolved_data_dir.is_absolute():
            resolved_data_dir = (base_dir / resolved_data_dir).resolve()

        cfg = resolve_year_config(base_dir, year=year, data_dir=resolved_data_dir)
        resolved_input = cfg.processed_dir / "ingested.csv"
        target_year = int(extract_base_year(cfg.year))

    output_path, manifest = run_bertweet_sentiment(
        year=target_year,
        output_partition=(cfg.year if not input_file else str(target_year)),
        input_path=resolved_input,
        output_root=base_dir / "sentiment",
        model_id=model,
        batch_size=batch_size,
        dry_run=dry_run,
        allow_fallback=allow_fallback,
        device=device,
        logger=typer.echo,
    )

    if dry_run:
        typer.echo("sentiment dry-run completed")
    else:
        typer.echo(f"sentiment output written to {output_path}")
    typer.echo(
        f"rows_in={manifest.record_counts['input']} rows_out={manifest.record_counts['output']} notes={len(manifest.notes)}"
    )
