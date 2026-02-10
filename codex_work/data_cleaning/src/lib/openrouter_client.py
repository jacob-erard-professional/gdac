from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def call_openrouter(
    api_key: str,
    model: str,
    messages: List[Dict[str, str]],
    timeout: int = 30,
    response_format: Optional[Dict[str, Any]] = None,
    plugins: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.0,
    }
    if response_format:
        payload["response_format"] = response_format
    if plugins:
        payload["plugins"] = plugins
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        OPENROUTER_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8")
        raise RuntimeError(f"OpenRouter HTTP error: {exc.code} {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenRouter connection error: {exc.reason}") from exc
