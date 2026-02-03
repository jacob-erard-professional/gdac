import json
from pathlib import Path


def run(rows, year: str, out_dir: Path) -> Path:
    sample = [{"sentiment": r.get("sentiment_label"), "retweets": r.get("retweet_count")} for r in rows[:1000]]
    out = out_dir / "relationship_metrics.json"
    out.write_text(json.dumps({"year": year, "sample": sample}, indent=2), encoding="utf-8")
    return out
