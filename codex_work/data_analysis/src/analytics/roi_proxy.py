import json
from pathlib import Path


def _to_int(value) -> int:
    if value in (None, ""):
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return 0


def run(rows, year: str, out_dir: Path) -> Path:
    engagement = 0
    for r in rows:
        engagement += _to_int(r.get("retweet_count")) + _to_int(r.get("favorite_count"))
    out = out_dir / "roi_proxy_metrics.json"
    out.write_text(json.dumps({"year": year, "engagement_proxy": engagement}, indent=2), encoding="utf-8")
    return out
