"""Analytics module for hashtag frequency computations."""

import json
from collections import Counter
from pathlib import Path


def run(rows, year: str, out_dir: Path) -> Path:
    counts = Counter()
    for row in rows:
        for tag in (row.get("hashtags") or "").split("|"):
            if tag:
                counts[tag.lower()] += 1

    ordered = [
        {"hashtag": hashtag, "count": count}
        for hashtag, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]
    out = out_dir / "hashtags_frequency.json"
    out.write_text(json.dumps({"year": year, "hashtags": ordered}, indent=2), encoding="utf-8")
    return out
