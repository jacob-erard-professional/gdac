import json
from pathlib import Path


def run(rows, year: str, out_dir: Path) -> Path:
    engagement = 0
    for r in rows:
        engagement += int(r.get("retweet_count") or 0) + int(r.get("favorite_count") or 0)
    out = out_dir / "roi_proxy_metrics.json"
    out.write_text(json.dumps({"year": year, "engagement_proxy": engagement}, indent=2), encoding="utf-8")
    return out
