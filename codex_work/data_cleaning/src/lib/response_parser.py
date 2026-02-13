from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from src.models.schemas import ClassificationResult, clamp_confidence, ensure_rationale


def _extract_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in response")
        return json.loads(match.group(0))


def parse_response(content: str, prompt_version: str | None = None) -> ClassificationResult:
    payload = _extract_json(content)
    is_about = bool(payload.get("is_about_brand"))
    confidence = clamp_confidence(payload.get("confidence"))
    rationale = ensure_rationale(payload.get("rationale"))
    if not rationale:
        raise ValueError("Rationale is required")
    return ClassificationResult(
        is_about_brand=is_about,
        confidence=confidence,
        rationale=rationale,
        prompt_version=prompt_version,
    )


def parse_batch_response(content: str) -> List[Dict[str, Any]]:
    payload = _extract_json(content)
    results = payload.get("results")
    if not isinstance(results, list):
        raise ValueError("Batch response must include results array")
    normalized = []
    for item in results:
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "id": int(item.get("id")),
                "is_about_brand": bool(item.get("is_about_brand")),
                "confidence": clamp_confidence(item.get("confidence")),
                "rationale": ensure_rationale(item.get("rationale")),
            }
        )
    return normalized


def parse_brand_list_batch_response(content: str) -> List[Dict[str, Any]]:
    payload = _extract_json(content)
    results = payload.get("results")
    if not isinstance(results, list):
        raise ValueError("Batch response must include results array")
    normalized = []
    for item in results:
        if not isinstance(item, dict):
            continue
        raw_id = item.get("id")
        if raw_id is None:
            continue
        normalized.append(
            {
                "id": int(raw_id),
                "category": str(item.get("category", "no_brand")),
                "assigned_brand": str(item.get("assigned_brand", "") or ""),
                "suggested_brand": str(item.get("suggested_brand", "") or ""),
                "confidence": clamp_confidence(item.get("confidence")),
                "rationale": ensure_rationale(item.get("rationale")),
            }
        )
    return normalized
