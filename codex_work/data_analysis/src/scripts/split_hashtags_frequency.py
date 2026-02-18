"""Utility script for split hashtags frequency operations."""

from pathlib import Path

import json
import typer

app = typer.Typer(add_completion=False)


@app.command()
def main(
    year: str = typer.Option(..., "--year", help="Year under outputs/analytics/<year>"),
    top_n: int = typer.Option(..., "--top-n", min=1, help="Number of hashtag rows to keep"),
    input_name: str = typer.Option("hashtags_frequency.json", "--input-name", help="Input JSON filename"),
    output_name: str = typer.Option(
        None,
        "--output-name",
        help="Output JSON filename (default: <input_stem>_top<top_n>.json)",
    ),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite output file if it exists"),
) -> None:
    base_dir = Path(__file__).resolve().parents[2]
    analytics_dir = base_dir / "outputs" / "analytics" / year
    input_path = analytics_dir / input_name

    if not input_path.exists():
        raise typer.BadParameter(f"Input file not found: {input_path}")

    out_name = output_name or f"{Path(input_name).stem}_top{top_n}.json"
    output_path = analytics_dir / out_name
    if output_path.exists() and not overwrite:
        raise typer.BadParameter(f"Output file already exists: {output_path}. Use --overwrite to replace it.")

    payload = json.loads(input_path.read_text(encoding="utf-8"))
    hashtags = payload.get("hashtags", [])
    if not isinstance(hashtags, list):
        raise typer.BadParameter(f"Input file has invalid 'hashtags' shape: expected list in {input_path}")

    payload["hashtags"] = hashtags[:top_n]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    typer.echo(f"Wrote {len(payload['hashtags'])} hashtag rows to {output_path}")


if __name__ == "__main__":
    app()
