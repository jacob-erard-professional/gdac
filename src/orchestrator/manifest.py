from datetime import datetime, UTC

from src.common.io.storage import write_json


def write_manifest(path: str, payload: dict) -> None:
    payload = {
        **payload,
        "written_at": datetime.now(UTC).isoformat(),
    }
    write_json(path, payload)
