import json
from datetime import datetime, UTC
from pathlib import Path


def write_json_log(path: str, level: str, message: str, **fields: object) -> None:
    record = {
        "timestamp": datetime.now(UTC).isoformat(),
        "level": level,
        "message": message,
        **fields,
    }
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
