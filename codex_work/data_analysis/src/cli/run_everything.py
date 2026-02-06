from pathlib import Path

import typer

from src.pipeline.config import RunRequest
from src.pipeline.orchestrator import run_pipeline
from src.pipeline.path_resolution import resolve_year_config

VALID_EXCLUDES = {
    "sentiment",
    "ad-sentiment",
    "deep-sentiment",
    "parent-company-deep-sentiment",
    "group-brands",
    "group-parent-companies",
}


def run_everything_command(
    year: str = typer.Option(None, "--year"),
    data_dir: Path = typer.Option(None, "--data-dir"),
    exclude: list[str] = typer.Option(
        [],
        "--exclude",
        help="Repeatable. One of: sentiment, ad-sentiment, deep-sentiment, parent-company-deep-sentiment, group-brands, group-parent-companies",
    ),
    sentiment_model: str = typer.Option(
        "finiteautomata/bertweet-base-sentiment-analysis",
        "--sentiment-model",
    ),
    sentiment_batch_size: int = typer.Option(64, "--sentiment-batch-size", min=1, max=4096),
    sentiment_device: str = typer.Option("cuda", "--sentiment-device"),
    deep_sentiment_model: str = typer.Option(
        "SamLowe/roberta-base-go_emotions",
        "--deep-sentiment-model",
    ),
    deep_sentiment_batch_size: int = typer.Option(64, "--deep-sentiment-batch-size", min=1, max=4096),
    deep_sentiment_device: str = typer.Option("cuda", "--deep-sentiment-device"),
    deep_sentiment_label_map_file: Path = typer.Option(None, "--deep-sentiment-label-map-file"),
    grouping_model: str = typer.Option("openai/gpt-4.1-mini", "--grouping-model"),
    request_delay: float = typer.Option(2.5, "--request-delay", min=2.5),
    max_rate_limit_retries: int = typer.Option(12, "--max-rate-limit-retries", min=12),
    initial_backoff: float = typer.Option(2.0, "--initial-backoff", min=2.0),
):
    if bool(year) == bool(data_dir):
        raise typer.BadParameter("Provide exactly one of --year or --data-dir")

    excluded = {item.strip().lower() for item in exclude}
    invalid = sorted(excluded.difference(VALID_EXCLUDES))
    if invalid:
        raise typer.BadParameter(f"Unknown --exclude value(s): {', '.join(invalid)}")

    run_sentiment = "sentiment" not in excluded
    run_ad_sentiment = "ad-sentiment" not in excluded
    run_deep_sentiment = "deep-sentiment" not in excluded
    run_parent_company_deep_sentiment = "parent-company-deep-sentiment" not in excluded
    run_group_brands = "group-brands" not in excluded
    run_group_parent_companies = "group-parent-companies" not in excluded

    if run_ad_sentiment and not run_sentiment:
        raise typer.BadParameter("ad-sentiment requires sentiment. Remove 'sentiment' from --exclude.")
    if run_parent_company_deep_sentiment and not run_deep_sentiment:
        raise typer.BadParameter(
            "parent-company-deep-sentiment requires deep-sentiment. Remove 'deep-sentiment' from --exclude."
        )
    if run_parent_company_deep_sentiment and not run_group_parent_companies:
        raise typer.BadParameter(
            "parent-company-deep-sentiment requires group-parent-companies. Remove 'group-parent-companies' from --exclude."
        )

    base_dir = Path(__file__).resolve().parents[2]
    resolved_data_dir = data_dir
    if resolved_data_dir and not resolved_data_dir.is_absolute():
        resolved_data_dir = (base_dir / resolved_data_dir).resolve()

    cfg = resolve_year_config(base_dir, year=year, data_dir=resolved_data_dir)
    resolved_label_map = deep_sentiment_label_map_file
    if resolved_label_map and not resolved_label_map.is_absolute():
        resolved_label_map = (base_dir / resolved_label_map).resolve()

    req = RunRequest(
        mode="full_year",
        stage=None,
        year=cfg.year,
        data_dir=resolved_data_dir,
        deterministic=True,
        with_sentiment=run_sentiment,
        with_ad_sentiment=run_ad_sentiment,
        sentiment_model=sentiment_model,
        sentiment_batch_size=sentiment_batch_size,
        sentiment_dry_run=False,
        sentiment_allow_fallback=False,
        sentiment_device=sentiment_device,
        with_deep_sentiment=run_deep_sentiment,
        deep_sentiment_model=deep_sentiment_model,
        deep_sentiment_batch_size=deep_sentiment_batch_size,
        deep_sentiment_dry_run=False,
        deep_sentiment_label_map_file=resolved_label_map,
        deep_sentiment_device=deep_sentiment_device,
        with_parent_company_deep_sentiment=False,
    )

    typer.echo(f"[run-everything] starting core pipeline for year={cfg.year}")
    results = run_pipeline(base_dir, req)
    for result in results:
        typer.echo(f"[run-everything] year={result.year} mode={result.mode} status={result.status}")

    if run_group_brands:
        try:
            from src.agents.brand_grouping_agent import run_brand_grouping
        except ModuleNotFoundError as exc:
            raise typer.BadParameter("Missing dependency for brand agent. Install requirements in your venv first.") from exc

        hashtags_path = cfg.analytics_dir / "hashtags_frequency.json"
        if not hashtags_path.exists():
            raise typer.BadParameter(f"Input file not found for brand grouping: {hashtags_path}")
        typer.echo("[run-everything] running group-brands")
        run_brand_grouping(
            hashtags_path=hashtags_path,
            output_path=cfg.analytics_dir / "brand_groups.json",
            model=grouping_model,
            request_delay_seconds=request_delay,
            max_rate_limit_retries=max_rate_limit_retries,
            initial_backoff_seconds=initial_backoff,
        )

    if run_group_parent_companies:
        try:
            from src.agents.parent_company_grouping_agent import run_parent_company_grouping
        except ModuleNotFoundError as exc:
            raise typer.BadParameter(
                "Missing dependency for parent company agent. Install requirements in your venv first."
            ) from exc

        brand_groups_path = cfg.analytics_dir / "brand_groups.json"
        if not brand_groups_path.exists():
            raise typer.BadParameter(
                f"Input file not found for parent-company grouping: {brand_groups_path}. "
                "Run without excluding group-brands, or create this file first."
            )
        typer.echo("[run-everything] running group-parent-companies")
        run_parent_company_grouping(
            brand_groups_path=brand_groups_path,
            output_path=cfg.analytics_dir / "parent_company_groups.json",
            model=grouping_model,
            request_delay_seconds=request_delay,
            max_rate_limit_retries=max_rate_limit_retries,
            initial_backoff_seconds=initial_backoff,
        )

    if run_parent_company_deep_sentiment:
        typer.echo("[run-everything] running parent-company-deep-sentiment")
        from src.sentiment.parent_company_deep_impact import run_parent_company_deep_sentiment_analysis

        deep_path = base_dir / "sentiment" / "deep" / cfg.year / "deep_sentiment.json"
        if not deep_path.exists():
            raise typer.BadParameter(
                f"Deep sentiment file not found: {deep_path}. Run without excluding deep-sentiment."
            )
        parent_groups_path = cfg.analytics_dir / "parent_company_groups.json"
        if not parent_groups_path.exists():
            raise typer.BadParameter(
                f"Parent company groups not found: {parent_groups_path}. Run without excluding group-parent-companies."
            )
        run_parent_company_deep_sentiment_analysis(
            year=int(cfg.year),
            deep_sentiment_path=deep_path,
            enriched_path=cfg.enriched_dir / "enriched.csv",
            parent_groups_path=parent_groups_path,
            output_dir=cfg.analytics_dir,
            min_tweets=1,
            tweet_map_path=cfg.analytics_dir / "parent_company_tweet_map.json",
        )

    typer.echo("[run-everything] complete")
