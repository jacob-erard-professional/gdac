"""Pipeline module for sentiment orchestration and execution."""

from src.pipeline.config import extract_base_year
from src.sentiment.bertweet import DEFAULT_MODEL_ID, run_bertweet_sentiment


def run(
    config,
    *,
    model_id: str = DEFAULT_MODEL_ID,
    batch_size: int = 64,
    dry_run: bool = False,
    allow_fallback: bool = False,
    device: str = "cuda",
):
    base_dir = config.processed_dir.parents[2]
    input_path = config.processed_dir / "ingested.csv"
    _output_path, manifest = run_bertweet_sentiment(
        year=int(extract_base_year(config.year)),
        output_partition=config.year,
        input_path=input_path,
        output_root=base_dir / "sentiment",
        model_id=model_id,
        batch_size=batch_size,
        dry_run=dry_run,
        allow_fallback=allow_fallback,
        device=device,
        logger=print,
    )
    return manifest
