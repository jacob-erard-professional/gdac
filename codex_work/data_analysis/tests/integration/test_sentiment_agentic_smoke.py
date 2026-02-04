from pathlib import Path

from src.agents.sentiment.config import RuntimeConfig
from src.agents.sentiment.orchestrator import run_sentiment_for_config


def test_sentiment_agentic_smoke(tmp_path: Path):
    cleaned = tmp_path / "data" / "processed" / "2024" / "cleaned.csv"
    cleaned.parent.mkdir(parents=True, exist_ok=True)
    cleaned.write_text(
        "id,created_at,text,author_id\n"
        "1,2024-02-11 10:00:00,I love this ad,u1\n"
        "2,2024-02-11 10:01:00,yeah right this is great,u2\n",
        encoding="utf-8",
    )
    analytics_dir = tmp_path / "outputs" / "analytics" / "2024"

    records, summary, manifest = run_sentiment_for_config(
        year="2024",
        cleaned_csv=cleaned,
        analytics_dir=analytics_dir,
        runtime_cfg=RuntimeConfig(dry_run=True),
    )

    assert records.exists()
    assert summary.exists()
    assert manifest.record_counts["output"] == 2
