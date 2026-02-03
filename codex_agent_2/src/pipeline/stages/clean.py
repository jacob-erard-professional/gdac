from __future__ import annotations

import json
from pathlib import Path


SCHEMA_VERSION = "1.0.0"


def run(input_paths: list[str], output_paths: list[str], config: dict, dry_run: bool) -> dict:
    source = Path(input_paths[0])
    target = Path(output_paths[0])
    if dry_run:
        return {"status": "dry_run", "reads": [str(source)], "writes": [str(target)], "schema_version": SCHEMA_VERSION}

    target.parent.mkdir(parents=True, exist_ok=True)
    cleaned = []
    if source.exists() and source.read_text().strip():
        for line in source.read_text().splitlines():
            row = json.loads(line)
            row["text"] = row.get("text", "").strip()
            cleaned.append(row)

    target.write_text("\n".join(json.dumps(row, sort_keys=True) for row in cleaned))
    return {"status": "succeeded", "outputs": [str(target)], "schema_version": SCHEMA_VERSION}
