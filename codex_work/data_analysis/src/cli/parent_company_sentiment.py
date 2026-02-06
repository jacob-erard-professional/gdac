from pathlib import Path

import typer

from src.pipeline.path_resolution import resolve_year_config
from src.sentiment.parent_company_impact import run_parent_company_sentiment_analysis


def parent_company_sentiment_command(
    year: str = typer.Option(None, "--year"),
    data_dir: Path = typer.Option(None, "--data-dir"),
    sentiment_file: Path = typer.Option(None, "--sentiment-file"),
    enriched_file: Path = typer.Option(None, "--enriched-file"),
    parent_groups_file: Path = typer.Option(None, "--parent-groups-file"),
    tweet_map_file: Path = typer.Option(None, "--tweet-map-file"),
    output_dir: Path = typer.Option(None, "--output-dir"),
    min_tweets: int = typer.Option(1, "--min-tweets", min=1),
):
    if bool(year) == bool(data_dir):
        raise typer.BadParameter("Provide exactly one of --year or --data-dir")

    base_dir = Path(__file__).resolve().parents[2]
    resolved_data_dir = data_dir
    if resolved_data_dir and not resolved_data_dir.is_absolute():
        resolved_data_dir = (base_dir / resolved_data_dir).resolve()

    cfg = resolve_year_config(base_dir, year=year, data_dir=resolved_data_dir)

    resolved_sentiment = sentiment_file or (base_dir / "sentiment" / "bertweet" / cfg.year / "sentiment.json")
    resolved_enriched = enriched_file or (cfg.enriched_dir / "enriched.csv")
    resolved_parent_groups = parent_groups_file or (cfg.analytics_dir / "parent_company_groups.json")
    resolved_output_dir = output_dir or cfg.analytics_dir
    resolved_tweet_map = tweet_map_file or (cfg.analytics_dir / "parent_company_tweet_map.json")

    if not resolved_sentiment.is_absolute():
        resolved_sentiment = (base_dir / resolved_sentiment).resolve()
    if not resolved_enriched.is_absolute():
        resolved_enriched = (base_dir / resolved_enriched).resolve()
    if not resolved_parent_groups.is_absolute():
        resolved_parent_groups = (base_dir / resolved_parent_groups).resolve()
    if not resolved_output_dir.is_absolute():
        resolved_output_dir = (base_dir / resolved_output_dir).resolve()
    if tweet_map_file and not resolved_tweet_map.is_absolute():
        resolved_tweet_map = (base_dir / resolved_tweet_map).resolve()
    if not resolved_tweet_map.exists():
        resolved_tweet_map = None

    outputs, manifest = run_parent_company_sentiment_analysis(
        year=int(cfg.year),
        sentiment_path=resolved_sentiment,
        enriched_path=resolved_enriched,
        parent_groups_path=resolved_parent_groups,
        tweet_map_path=resolved_tweet_map,
        output_dir=resolved_output_dir,
        min_tweets=min_tweets,
    )

    typer.echo(f"parent company sentiment joined output written to {outputs.joined_parquet}")
    typer.echo(f"parent company sentiment summary written to {outputs.summary_json}")
    typer.echo(f"rows_in={manifest.record_counts['input']} rows_out={manifest.record_counts['output']}")
