from src.sentiment.parent_company_deep_impact import run_parent_company_deep_sentiment_analysis


def run(config, *, min_tweets: int = 1):
    base_dir = config.processed_dir.parents[2]
    deep_sentiment_path = base_dir / "sentiment" / "deep" / config.year / "deep_sentiment.json"
    enriched_path = config.enriched_dir / "enriched.csv"
    parent_groups_path = config.analytics_dir / "parent_company_groups.json"
    output_dir = config.analytics_dir
    tweet_map_path = config.analytics_dir.parents[1] / "aux" / config.year / "parent_company_tweet_map.json"
    if not tweet_map_path.exists():
        try:
            from src.utils.tweet_company_map import build_brand_tweet_map, build_parent_company_tweet_map
        except ModuleNotFoundError:
            build_brand_tweet_map = None
            build_parent_company_tweet_map = None
        if build_brand_tweet_map and build_parent_company_tweet_map:
            brand_groups_path = config.analytics_dir / "brand_groups.json"
            brand_map_path = config.analytics_dir.parents[1] / "aux" / config.year / "brand_tweet_map.json"
            if brand_groups_path.exists() and enriched_path.exists():
                if not brand_map_path.exists():
                    build_brand_tweet_map(
                        enriched_path=enriched_path,
                        brand_groups_path=brand_groups_path,
                        output_path=brand_map_path,
                        year=int(config.year),
                    )
                if brand_map_path.exists() and parent_groups_path.exists():
                    build_parent_company_tweet_map(
                        brand_tweet_map_path=brand_map_path,
                        parent_company_groups_path=parent_groups_path,
                        output_path=tweet_map_path,
                        year=int(config.year),
                    )
    if not tweet_map_path.exists():
        tweet_map_path = None

    _outputs, manifest = run_parent_company_deep_sentiment_analysis(
        year=int(config.year),
        deep_sentiment_path=deep_sentiment_path,
        enriched_path=enriched_path,
        parent_groups_path=parent_groups_path,
        output_dir=output_dir,
        min_tweets=min_tweets,
        tweet_map_path=tweet_map_path,
    )
    return manifest
