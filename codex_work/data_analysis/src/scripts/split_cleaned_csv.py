"""Utility script for split cleaned csv operations."""

from pathlib import Path

import pandas as pd
import typer

app = typer.Typer(add_completion=False)


@app.command()
def main(
    year: str = typer.Option(..., "--year", help="Year directory under data/processed/<year>"),
    rows: int = typer.Option(..., "--rows", min=1, help="Number of rows to put in the first split"),
    input_name: str = typer.Option("cleaned.csv", "--input-name", help="Input CSV filename"),
    first_output_name: str = typer.Option(
        None,
        "--first-output-name",
        help="Output filename for the first split (default: cleaned_first_<rows>.csv)",
    ),
    chunk_size: int = typer.Option(50_000, "--chunk-size", min=1, help="Rows to read per chunk"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing output files"),
) -> None:
    base_dir = Path(__file__).resolve().parents[2]
    year_dir = base_dir / "data" / "processed" / year
    input_path = year_dir / input_name

    if not input_path.exists():
        raise typer.BadParameter(f"Input file not found: {input_path}")

    first_name = first_output_name or f"cleaned_first_{rows}.csv"
    first_output_path = year_dir / first_name

    if not overwrite:
        existing = [p for p in (first_output_path,) if p.exists()]
        if existing:
            existing_paths = ", ".join(str(path) for path in existing)
            raise typer.BadParameter(
                f"Output file(s) already exist: {existing_paths}. Use --overwrite to replace."
            )

    first_output_path.parent.mkdir(parents=True, exist_ok=True)

    if overwrite:
        for output_path in (first_output_path,):
            if output_path.exists():
                output_path.unlink()

    first_header_written = False
    rows_left_for_first = rows
    columns = None
    total_rows = 0

    for chunk in pd.read_csv(input_path, chunksize=chunk_size):
        if columns is None:
            columns = list(chunk.columns)
        total_rows += len(chunk)

        if rows_left_for_first > 0:
            first_chunk = chunk.iloc[:rows_left_for_first]

            if not first_chunk.empty:
                first_chunk.to_csv(first_output_path, mode="a", index=False, header=not first_header_written)
                first_header_written = True
                rows_left_for_first -= len(first_chunk)

    if columns is None:
        raise typer.BadParameter(f"Input file is empty: {input_path}")

    if not first_header_written:
        pd.DataFrame(columns=columns).to_csv(first_output_path, index=False)

    typer.echo(f"Input rows: {total_rows}")
    typer.echo(f"First split rows: {min(rows, total_rows)} -> {first_output_path}")


if __name__ == "__main__":
    app()
