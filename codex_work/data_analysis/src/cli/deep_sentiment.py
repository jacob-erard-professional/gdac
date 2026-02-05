from pathlib import Path

import typer

from src.pipeline.path_resolution import resolve_year_config
from src.sentiment.deep_emotion import DEFAULT_MODEL_ID, run_deep_sentiment


def deep_sentiment_command(
    year: str = typer.Option(None, "--year", help="Year for partitioning output and default input resolution"),
    data_dir: Path = typer.Option(None, "--data-dir", help="Raw year directory used to resolve year"),
    input_file: Path = typer.Option(None, "--input-file", help="Explicit CSV or Parquet input path"),
    model: str = typer.Option(DEFAULT_MODEL_ID, "--model", help="Hugging Face model identifier"),
    batch_size: int = typer.Option(64, "--batch-size", min=1),
    dry_run: bool = typer.Option(False, "--dry-run"),
    label_map_file: Path = typer.Option(
        None,
        "--label-map-file",
        help="Optional JSON file mapping model labels to required emotions.",
    ),
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
        resolved_input = cfg.processed_dir / "cleaned.csv"
        target_year = int(cfg.year)

    resolved_label_map_file = label_map_file
    if resolved_label_map_file and not resolved_label_map_file.is_absolute():
        resolved_label_map_file = (base_dir / resolved_label_map_file).resolve()

    output_path, manifest = run_deep_sentiment(
        year=target_year,
        input_path=resolved_input,
        output_root=base_dir / "sentiment",
        model_id=model,
        batch_size=batch_size,
        dry_run=dry_run,
        label_map_file=resolved_label_map_file,
        logger=typer.echo,
    )

    if dry_run:
        typer.echo("deep sentiment dry-run completed")
    else:
        typer.echo(f"deep sentiment output written to {output_path}")

    typer.echo(
        f"rows_in={manifest.record_counts['input']} rows_out={manifest.record_counts['output']} notes={len(manifest.notes)}"
    )
