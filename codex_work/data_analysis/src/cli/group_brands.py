from pathlib import Path

import typer

from src.agents.rate_limit_policy import (
    MIN_INITIAL_BACKOFF_SECONDS,
    MIN_MAX_RATE_LIMIT_RETRIES,
    MIN_REQUEST_DELAY_SECONDS,
)


def group_brands_command(
    year: str = typer.Option(..., "--year", help="Year to read from outputs/analytics/<year>/"),
    input_file: Path | None = typer.Option(
        None,
        "--input-file",
        help="Optional explicit hashtags_frequency.json path",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        help="Optional explicit output file path",
    ),
    enriched_file: Path | None = typer.Option(
        None,
        "--enriched-file",
        help="Optional enriched.csv path for tweet-to-brand mapping output",
    ),
    model: str = typer.Option(
        "openai/gpt-4.1-mini",
        "--model",
        help="OpenRouter model id",
    ),
    chunk_size: int = typer.Option(60, "--chunk-size", min=20, max=500),
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
    hints_file: Path = typer.Option(
        None,
        "--hints-file",
        help="Optional JSON file with hashtag/brand hints.",
    ),
):
    try:
        from src.agents.brand_grouping_agent import run_brand_grouping
    except ModuleNotFoundError as exc:
        raise typer.BadParameter(
            "Missing dependency for brand agent. Install requirements in your venv first."
        ) from exc

    base_dir = Path(__file__).resolve().parents[2]
    resolved_input = input_file or (base_dir / "outputs" / "analytics" / year / "hashtags_frequency.json")
    resolved_output = output_file or (base_dir / "outputs" / "analytics" / year / "brand_groups.json")
    resolved_enriched = enriched_file or (base_dir / "data" / "enriched" / year / "enriched.csv")
    aux_dir = base_dir / "outputs" / "aux" / year
    tweet_map_output = aux_dir / "brand_tweet_map.json"

    if not resolved_input.exists():
        raise typer.BadParameter(f"Input file not found: {resolved_input}")

    out = run_brand_grouping(
        hashtags_path=resolved_input,
        output_path=resolved_output,
        model=model,
        chunk_size=chunk_size,
        resume=resume,
        request_delay_seconds=request_delay,
        max_rate_limit_retries=max_rate_limit_retries,
        initial_backoff_seconds=initial_backoff,
        hints_path=hints_file,
    )
    typer.echo(f"brand grouping written to {out}")

    if not resolved_enriched.exists():
        raise typer.BadParameter(f"Enriched file not found for tweet mapping: {resolved_enriched}")
    from src.utils.tweet_company_map import build_brand_tweet_map

    tweet_map = build_brand_tweet_map(
        enriched_path=resolved_enriched,
        brand_groups_path=resolved_output,
        output_path=tweet_map_output,
        year=int(year),
    )
    typer.echo(f"brand tweet map written to {tweet_map}")
