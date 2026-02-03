import json
from collections import Counter
from pathlib import Path


def run(rows, year: str, out_dir: Path) -> Path:
    tags = Counter()
    for r in rows:
        for t in (r.get("hashtags") or "").split('|'):
            if t:
                tags[t] += 1
    out = out_dir / "text_network_metrics.json"
    out.write_text(json.dumps({"year": year, "hashtags": tags}, indent=2), encoding="utf-8")
    return out
