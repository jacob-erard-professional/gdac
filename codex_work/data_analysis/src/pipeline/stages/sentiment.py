from src.sentiment.bertweet import DEFAULT_MODEL_ID, run_bertweet_sentiment


def run(
    config,
    *,
    model_id: str = DEFAULT_MODEL_ID,
    batch_size: int = 64,
    dry_run: bool = False,
    allow_fallback: bool = False,
):
    base_dir = config.processed_dir.parents[2]
    input_path = config.processed_dir / "cleaned.csv"
    _output_path, manifest = run_bertweet_sentiment(
        year=int(config.year),
        input_path=input_path,
        output_root=base_dir / "sentiment",
        model_id=model_id,
        batch_size=batch_size,
        dry_run=dry_run,
        allow_fallback=allow_fallback,
        logger=print,
    )
    return manifest
