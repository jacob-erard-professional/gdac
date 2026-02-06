from pathlib import Path

from src.sentiment.deep_emotion import DEFAULT_MODEL_ID, run_deep_sentiment


def run(
    config,
    *,
    model_id: str = DEFAULT_MODEL_ID,
    batch_size: int = 64,
    dry_run: bool = False,
    label_map_file: Path | None = None,
    device: str = "cuda",
):
    base_dir = config.processed_dir.parents[2]
    input_path = config.processed_dir / "cleaned.csv"

    resolved_label_map = label_map_file
    if resolved_label_map and not resolved_label_map.is_absolute():
        resolved_label_map = (base_dir / resolved_label_map).resolve()

    _output_path, manifest = run_deep_sentiment(
        year=int(config.year),
        input_path=input_path,
        output_root=base_dir / "sentiment",
        model_id=model_id,
        batch_size=batch_size,
        dry_run=dry_run,
        label_map_file=resolved_label_map,
        device=device,
        logger=print,
    )
    return manifest
