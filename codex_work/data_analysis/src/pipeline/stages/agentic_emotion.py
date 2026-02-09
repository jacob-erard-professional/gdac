import json

from src.agents.agentic_emotion_agent import run_agentic_emotion
from src.pipeline.stage_runtime import make_manifest


def run(
    config,
    *,
    model: str,
    batch_size: int,
    dry_run: bool,
    brand_filter: str | None,
    examples_per_emotion: int,
):
    enriched_path = config.enriched_dir / "enriched.csv"
    output_dir = config.analytics_dir
    brands = [b.strip().lower() for b in (brand_filter or "").split(",") if b.strip()]

    summary_path, examples_path = run_agentic_emotion(
        year=int(config.year),
        enriched_path=enriched_path,
        output_dir=output_dir,
        model=model,
        batch_size=batch_size,
        brand_filter=brands,
        dry_run=dry_run,
        resume=True,
        examples_per_emotion=examples_per_emotion,
    )

    output_files = [] if dry_run else [summary_path, examples_path]
    count_out = 0
    if not dry_run and summary_path.exists():
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        count_out = int(payload.get("total_rows", 0))

    return make_manifest([enriched_path], output_files, count_out, count_out)
