from pathlib import Path

from src.pipeline.config import RunRequest
from src.pipeline.orchestrator import run_pipeline


def test_full_year_with_sentiment_writes_sentiment_artifacts(tmp_path: Path):
    raw = tmp_path / "data" / "raw" / "2024"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "tweets.csv").write_text(
        "tweet_id,created_at,text,user_id\n"
        "1,2024-02-11 10:00:00,#x great,u1\n",
        encoding="utf-8",
    )

    req = RunRequest(
        mode="full_year",
        stage=None,
        year="2024",
        data_dir=None,
        with_sentiment=True,
        sentiment_dry_run=True,
    )
    result = run_pipeline(tmp_path, req)[0]

    stage_names = [s["stage"] for s in result.stages]
    assert "sentiment" in stage_names
    assert (tmp_path / "outputs" / "analytics" / "2024" / "sentiment_agentic.jsonl").exists()
