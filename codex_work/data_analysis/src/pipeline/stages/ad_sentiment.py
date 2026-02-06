from src.sentiment.ad_impact import run_ad_sentiment_analysis


def run(config, *, min_tweets: int = 1):
    base_dir = config.processed_dir.parents[2]
    sentiment_path = base_dir / "sentiment" / "bertweet" / config.year / "sentiment.json"
    enriched_path = config.enriched_dir / "enriched.csv"
    output_dir = config.analytics_dir
    tweet_map_path = config.analytics_dir / "brand_tweet_map.json"
    if not tweet_map_path.exists():
        tweet_map_path = None

    _outputs, manifest = run_ad_sentiment_analysis(
        year=int(config.year),
        sentiment_path=sentiment_path,
        enriched_path=enriched_path,
        output_dir=output_dir,
        min_tweets=min_tweets,
        tweet_map_path=tweet_map_path,
        logger=print,
    )
    return manifest
