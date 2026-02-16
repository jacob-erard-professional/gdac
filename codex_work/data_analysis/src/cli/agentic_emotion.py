from pathlib import Path

import typer

from src.agents.agentic_emotion_agent import run_agentic_emotion
from src.agents.rate_limit_policy import (
    MIN_INITIAL_BACKOFF_SECONDS,
    MIN_MAX_RATE_LIMIT_RETRIES,
    MIN_REQUEST_DELAY_SECONDS,
)
from src.pipeline.config import extract_base_year
from src.pipeline.path_resolution import resolve_year_config


def agentic_emotion_command(
    year: str = typer.Option(None, "--year"),
    data_dir: Path = typer.Option(None, "--data-dir"),
    model: str = typer.Option(..., "--model", help="OpenRouter model id (required)"),
    batch_size: int = typer.Option(40, "--batch-size", min=1, max=200),
    brand_filter: str = typer.Option("", "--brand-filter", help="Comma-separated brand list"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    resume: bool = typer.Option(True, "--resume/--no-resume"),
    examples_per_emotion: int = typer.Option(3, "--examples-per-emotion", min=1, max=10),
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
    if bool(year) == bool(data_dir):
        raise typer.BadParameter("Provide exactly one of --year or --data-dir")

    base_dir = Path(__file__).resolve().parents[2]
    resolved_data_dir = data_dir
    if resolved_data_dir and not resolved_data_dir.is_absolute():
        resolved_data_dir = (base_dir / resolved_data_dir).resolve()

    cfg = resolve_year_config(base_dir, year=year, data_dir=resolved_data_dir)
    enriched_path = cfg.enriched_dir / "enriched.csv"
    output_dir = cfg.analytics_dir

    brands = [b.strip().lower() for b in brand_filter.split(",") if b.strip()]

    summary_path, examples_path = run_agentic_emotion(
        year=int(extract_base_year(cfg.year)),
        enriched_path=enriched_path,
        output_dir=output_dir,
        model=model,
        batch_size=batch_size,
        brand_filter=brands,
        dry_run=dry_run,
        request_delay_seconds=request_delay,
        max_rate_limit_retries=max_rate_limit_retries,
        initial_backoff_seconds=initial_backoff,
        resume=resume,
        examples_per_emotion=examples_per_emotion,
    )

    if dry_run:
        typer.echo("agentic emotion dry-run complete (no outputs written)")
        return
    typer.echo(f"agentic emotion summary written to {summary_path}")
    typer.echo(f"agentic emotion examples written to {examples_path}")
