import json
from collections import Counter
from pathlib import Path


def run(rows, year: str, out_dir: Path) -> Path:
    c = Counter(r.get("game_phase", "unknown") for r in rows)
    out = out_dir / "time_bucket_metrics.json"
    out.write_text(json.dumps({"year": year, "time_buckets": c}, indent=2), encoding="utf-8")
    return out
