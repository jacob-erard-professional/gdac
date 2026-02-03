from __future__ import annotations

import csv
import json
from pathlib import Path


SCHEMA_VERSION = "1.0.0"


def run(input_paths: list[str], output_paths: list[str], config: dict, dry_run: bool) -> dict:
    source = Path(input_paths[0])
    target = Path(output_paths[0])
    if dry_run:
        return {"status": "dry_run", "reads": [str(source)], "writes": [str(target)], "schema_version": SCHEMA_VERSION}

    target.parent.mkdir(parents=True, exist_ok=True)
    if source.exists() and source.suffix.lower() == ".csv":
        rows = []
        with source.open(newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                rows.append({"id": row.get("id"), "text": row.get("text", "")})
        target.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows))
    elif source.exists():
        target.write_text(source.read_text())
    else:
        # Bootstrap sample empty stream.
        target.write_text("")

    return {"status": "succeeded", "outputs": [str(target)], "schema_version": SCHEMA_VERSION}
