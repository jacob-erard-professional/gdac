from pathlib import Path

import typer


def group_parent_companies_command(
    year: str = typer.Option(..., "--year", help="Year to read from outputs/analytics/<year>/"),
    input_file: Path | None = typer.Option(
        None,
        "--input-file",
        help="Optional explicit brand_groups.json path",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        help="Optional explicit output file path",
    ),
    model: str = typer.Option(
        "openai/gpt-oss-120b:free",
        "--model",
        help="OpenRouter model id",
    ),
    chunk_size: int = typer.Option(40, "--chunk-size", min=10, max=500),
    request_delay: float = typer.Option(
        1.5, "--request-delay", min=0.0, help="Delay between LLM requests in seconds"
    ),
    max_rate_limit_retries: int = typer.Option(
        8, "--max-rate-limit-retries", min=0, help="Retries for HTTP 429/rate-limit errors"
    ),
    initial_backoff: float = typer.Option(
        2.0, "--initial-backoff", min=0.5, help="Initial exponential backoff in seconds"
    ),
):
    try:
        from src.agents.parent_company_grouping_agent import run_parent_company_grouping
    except ModuleNotFoundError as exc:
        raise typer.BadParameter(
            "Missing dependency for parent company agent. Install requirements in your venv first."
        ) from exc

    base_dir = Path(__file__).resolve().parents[2]
    resolved_input = input_file or (base_dir / "outputs" / "analytics" / year / "brand_groups.json")
    resolved_output = output_file or (base_dir / "outputs" / "analytics" / year / "parent_company_groups.json")

    if not resolved_input.exists():
        raise typer.BadParameter(f"Input file not found: {resolved_input}")

    out = run_parent_company_grouping(
        brand_groups_path=resolved_input,
        output_path=resolved_output,
        model=model,
        chunk_size=chunk_size,
        request_delay_seconds=request_delay,
        max_rate_limit_retries=max_rate_limit_retries,
        initial_backoff_seconds=initial_backoff,
    )
    typer.echo(f"parent company grouping written to {out}")
