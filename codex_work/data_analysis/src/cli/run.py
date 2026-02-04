from pathlib import Path
import typer
from src.pipeline.config import RunRequest
from src.pipeline.orchestrator import run_pipeline


def run_command(
    year: str = typer.Option(None, "--year"),
    data_dir: Path = typer.Option(None, "--data-dir"),
    stage: str = typer.Option(None, "--stage"),
    all_: bool = typer.Option(False, "--all"),
    with_sentiment: bool = typer.Option(False, "--with-sentiment"),
    with_ad_sentiment: bool = typer.Option(False, "--with-ad-sentiment"),
    sentiment_model: str = typer.Option(
        "finiteautomata/bertweet-base-sentiment-analysis",
        "--sentiment-model",
    ),
    sentiment_batch_size: int = typer.Option(64, "--sentiment-batch-size", min=1, max=4096),
    sentiment_dry_run: bool = typer.Option(False, "--sentiment-dry-run"),
    sentiment_allow_fallback: bool = typer.Option(False, "--sentiment-allow-fallback"),
    ad_sentiment_min_tweets: int = typer.Option(1, "--ad-sentiment-min-tweets", min=1),
):
    if bool(stage) == bool(all_):
        raise typer.BadParameter("Provide exactly one of --stage or --all")

    base_dir = Path(__file__).resolve().parents[2]
    resolved_data_dir = data_dir
    if resolved_data_dir and not resolved_data_dir.is_absolute():
        resolved_data_dir = (base_dir / resolved_data_dir).resolve()

    if stage:
        if with_sentiment or with_ad_sentiment:
            raise typer.BadParameter("--with-sentiment/--with-ad-sentiment are supported only with --all")
        if bool(year) == bool(resolved_data_dir):
            raise typer.BadParameter("Stage mode requires exactly one of --year or --data-dir")
        mode = 'stage'
    else:
        if year and resolved_data_dir:
            raise typer.BadParameter("Provide only one of --year or --data-dir with --all")
        if with_ad_sentiment and not with_sentiment:
            raise typer.BadParameter("--with-ad-sentiment requires --with-sentiment")
        mode = 'full_all_years' if not year and not resolved_data_dir else 'full_year'

    req = RunRequest(
        mode=mode,
        stage=stage,
        year=year,
        data_dir=resolved_data_dir,
        deterministic=True,
        with_sentiment=with_sentiment,
        with_ad_sentiment=with_ad_sentiment,
        sentiment_model=sentiment_model,
        sentiment_batch_size=sentiment_batch_size,
        sentiment_dry_run=sentiment_dry_run,
        sentiment_allow_fallback=sentiment_allow_fallback,
        ad_sentiment_min_tweets=ad_sentiment_min_tweets,
    )
    results = run_pipeline(base_dir, req)
    for result in results:
        typer.echo(f"year={result.year} mode={result.mode} status={result.status} stages={len(result.stages)}")
