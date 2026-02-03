import json
from pathlib import Path


def run(rows, year: str, out_dir: Path) -> Path:
    events = {}
    for r in rows:
        phase = r.get("game_phase", "unknown")
        events[phase] = events.get(phase, 0) + 1
    out = out_dir / "event_alignment_metrics.json"
    out.write_text(json.dumps({"year": year, "phase_counts": events}, indent=2), encoding="utf-8")
    return out
