import json
from collections import Counter
from pathlib import Path


def run(rows, year: str, out_dir: Path) -> Path:
    c = Counter(r.get("brand_tag", "unknown") for r in rows)
    out = out_dir / "volume_metrics.json"
    out.write_text(json.dumps({"year": year, "brand_volume": c}, indent=2), encoding="utf-8")
    return out
