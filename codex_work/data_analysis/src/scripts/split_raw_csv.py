from pathlib import Path

import pandas as pd
import typer

app = typer.Typer(add_completion=False)


@app.command()
def main(
    year: str = typer.Option(..., "--year", help="Year under data/raw/<year>"),
    rows: int = typer.Option(..., "--rows", min=1, help="Number of rows to keep"),
    input_name: str = typer.Option("tweets.csv", "--input-name", help="Input CSV filename"),
    output_name: str = typer.Option(
        None,
        "--output-name",
        help="Output CSV filename (default: <input_stem>_first_<rows>.csv)",
    ),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite output if it exists"),
) -> None:
    base_dir = Path(__file__).resolve().parents[2]
    input_path = base_dir / "data" / "raw" / year / input_name

    if not input_path.exists():
        raise typer.BadParameter(f"Input file not found: {input_path}")

    if output_name:
        out_name = output_name
    else:
        out_name = f"{Path(input_name).stem}_first_{rows}.csv"
    output_path = input_path.parent / out_name

    if output_path.exists() and not overwrite:
        raise typer.BadParameter(f"Output file already exists: {output_path}. Use --overwrite to replace it.")

    sample = pd.read_csv(input_path, nrows=rows)
    sample.to_csv(output_path, index=False)

    typer.echo(f"Wrote {len(sample)} rows to {output_path}")


if __name__ == "__main__":
    app()
