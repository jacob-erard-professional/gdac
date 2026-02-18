"""Analytics module for mention frequency computations."""

import json
import re
from collections import Counter
from pathlib import Path

MENTION_RE = re.compile(r"@([A-Za-z0-9_]{1,15})")


def run(rows, year: str, out_dir: Path) -> Path:
    counts = Counter()
    for row in rows:
        text = row.get("text") or ""
        for mention in MENTION_RE.findall(text):
            counts[mention.lower()] += 1

    ordered = [
        {"mention": mention, "count": count}
        for mention, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]
    out = out_dir / "mentions_frequency.json"
    out.write_text(json.dumps({"year": year, "mentions": ordered}, indent=2), encoding="utf-8")
    return out
