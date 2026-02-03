from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


SCHEMA_VERSION = "1.0.0"


def run(input_paths: list[str], output_paths: list[str], config: dict, dry_run: bool) -> dict:
    source = Path(input_paths[0])
    target = Path(output_paths[0])
    mappings_path = Path(config.get("normalized_mappings_path", "")) if config else None
    emotion_lexicon_path = Path(config.get("emotion_lexicon_path", "")) if config else None
    emotion_ml_path = Path(config.get("emotion_ml_path", "")) if config else None

    if dry_run:
        reads = [str(source)]
        if mappings_path and str(mappings_path):
            reads.append(str(mappings_path))
        return {"status": "dry_run", "reads": reads, "writes": [str(target)], "schema_version": SCHEMA_VERSION}

    canonical_map = {}
    if mappings_path and mappings_path.exists() and mappings_path.read_text().strip():
        payload = json.loads(mappings_path.read_text())
        for mapping in payload.get("mappings", []):
            canonical_map[mapping["raw_tag"].lower()] = mapping["canonical_tag"].lower()

    target.parent.mkdir(parents=True, exist_ok=True)
    counts = Counter()
    if source.exists() and source.read_text().strip():
        for item in json.loads(source.read_text()):
            raw = item["tag"].lower()
            canonical = canonical_map.get(raw, raw)
            counts[canonical] += item.get("frequency", 1)

    report = {
        "total_unique_hashtags": len(counts),
        "counts": dict(sorted(counts.items())),
    }

    if emotion_lexicon_path and emotion_lexicon_path.exists() and emotion_lexicon_path.read_text().strip():
        lexicon_payload = json.loads(emotion_lexicon_path.read_text())
        report["emotion_lexicon_summary"] = lexicon_payload.get("summary", {})
    if emotion_ml_path and emotion_ml_path.exists() and emotion_ml_path.read_text().strip():
        ml_payload = json.loads(emotion_ml_path.read_text())
        report["emotion_ml_summary"] = ml_payload.get("summary", {})

    target.write_text(json.dumps(report, indent=2, sort_keys=True))
    return {"status": "succeeded", "outputs": [str(target)], "schema_version": SCHEMA_VERSION}
