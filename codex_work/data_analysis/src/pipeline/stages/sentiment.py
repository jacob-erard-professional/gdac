from src.agents.sentiment.config import AgentModelConfig, RuntimeConfig
from src.agents.sentiment.orchestrator import run_sentiment_for_config


def run(config, dry_run: bool = False, verbose: bool = False):
    cleaned = config.processed_dir / "cleaned.csv"
    _, _, manifest = run_sentiment_for_config(
        year=config.year,
        cleaned_csv=cleaned,
        analytics_dir=config.analytics_dir,
        model_cfg=AgentModelConfig(),
        runtime_cfg=RuntimeConfig(dry_run=dry_run, verbose=verbose),
    )
    return manifest

