import json
from pathlib import Path


def run(rows, year: str, out_dir: Path) -> Path:
    totals = {"positive": 0, "neutral": 0, "negative": 0}
    for r in rows:
        label = (r.get("sentiment_label") or "neutral").lower()
        if label not in totals:
            label = "neutral"
        totals[label] += 1
    out = out_dir / "sentiment_metrics.json"
    out.write_text(json.dumps({"year": year, "sentiment": totals}, indent=2), encoding="utf-8")
    return out
