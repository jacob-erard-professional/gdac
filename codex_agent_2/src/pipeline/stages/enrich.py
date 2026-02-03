from __future__ import annotations

import json
import re
from pathlib import Path


SCHEMA_VERSION = "1.0.0"
HASHTAG_RE = re.compile(r"#\\w+")


def run(input_paths: list[str], output_paths: list[str], config: dict, dry_run: bool) -> dict:
    source = Path(input_paths[0])
    target = Path(output_paths[0])
    if dry_run:
        return {"status": "dry_run", "reads": [str(source)], "writes": [str(target)], "schema_version": SCHEMA_VERSION}

    target.parent.mkdir(parents=True, exist_ok=True)
    candidates = []
    if source.exists() and source.read_text().strip():
        text = source.read_text()
        for line_idx, line in enumerate(text.splitlines(), start=1):
            row = json.loads(line)
            for tag in HASHTAG_RE.findall(row.get("text", "")):
                candidates.append(
                    {
                        "candidate_id": f"cand-{line_idx}-{tag.lower()}",
                        "tag": tag,
                        "normalized_token": tag.lower(),
                        "frequency": 1,
                        "contexts": [row.get("text", "")],
                    }
                )

    target.write_text(json.dumps(candidates, indent=2))
    return {"status": "succeeded", "outputs": [str(target)], "schema_version": SCHEMA_VERSION}
