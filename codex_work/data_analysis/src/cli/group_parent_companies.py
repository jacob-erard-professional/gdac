from pathlib import Path

import typer

from src.agents.rate_limit_policy import (
    MIN_INITIAL_BACKOFF_SECONDS,
    MIN_MAX_RATE_LIMIT_RETRIES,
    MIN_REQUEST_DELAY_SECONDS,
)


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
    enriched_file: Path | None = typer.Option(
        None,
        "--enriched-file",
        help="Optional enriched.csv path for tweet-to-parent mapping output",
    ),
    model: str = typer.Option(
        "openai/gpt-4.1-mini",
        "--model",
        help="OpenRouter model id",
    ),
    chunk_size: int = typer.Option(40, "--chunk-size", min=10, max=500),
    resume: bool = typer.Option(True, "--resume/--no-resume", help="Resume from existing partial results"),
    request_delay: float = typer.Option(
        MIN_REQUEST_DELAY_SECONDS,
        "--request-delay",
        min=MIN_REQUEST_DELAY_SECONDS,
        help="Delay between LLM requests in seconds (constitution minimum enforced).",
    ),
    max_rate_limit_retries: int = typer.Option(
        MIN_MAX_RATE_LIMIT_RETRIES,
        "--max-rate-limit-retries",
        min=MIN_MAX_RATE_LIMIT_RETRIES,
        help="Retries for HTTP 429/rate-limit errors (constitution minimum enforced).",
    ),
    initial_backoff: float = typer.Option(
        MIN_INITIAL_BACKOFF_SECONDS,
        "--initial-backoff",
        min=MIN_INITIAL_BACKOFF_SECONDS,
        help="Initial exponential backoff in seconds (constitution minimum enforced).",
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
    resolved_enriched = enriched_file or (base_dir / "data" / "enriched" / year / "enriched.csv")
    brand_tweet_map = resolved_output.with_name("brand_tweet_map.json")
    parent_tweet_map = resolved_output.with_name("parent_company_tweet_map.json")

    if not resolved_input.exists():
        raise typer.BadParameter(f"Input file not found: {resolved_input}")

    out = run_parent_company_grouping(
        brand_groups_path=resolved_input,
        output_path=resolved_output,
        model=model,
        chunk_size=chunk_size,
        resume=resume,
        request_delay_seconds=request_delay,
        max_rate_limit_retries=max_rate_limit_retries,
        initial_backoff_seconds=initial_backoff,
    )
    typer.echo(f"parent company grouping written to {out}")

    from src.utils.tweet_company_map import build_brand_tweet_map, build_parent_company_tweet_map

    if not brand_tweet_map.exists():
        if not resolved_enriched.exists():
            raise typer.BadParameter(f"Enriched file not found for tweet mapping: {resolved_enriched}")
        brand_tweet_map = build_brand_tweet_map(
            enriched_path=resolved_enriched,
            brand_groups_path=resolved_input,
            output_path=brand_tweet_map,
            year=int(year),
        )
        typer.echo(f"brand tweet map written to {brand_tweet_map}")

    parent_map = build_parent_company_tweet_map(
        brand_tweet_map_path=brand_tweet_map,
        parent_company_groups_path=resolved_output,
        output_path=parent_tweet_map,
        year=int(year),
    )
    typer.echo(f"parent company tweet map written to {parent_map}")
