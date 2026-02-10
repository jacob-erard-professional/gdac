from __future__ import annotations

import json
import sys
from datetime import datetime
from typing import Any, Dict


def log_event(event: str, payload: Dict[str, Any]) -> None:
    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event": event,
        **payload,
    }
    sys.stdout.write(json.dumps(record, sort_keys=True) + "\n")
    sys.stdout.flush()
