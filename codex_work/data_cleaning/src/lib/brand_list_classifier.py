from __future__ import annotations

from typing import Any, Callable, Dict, List

from src.lib.classifier import invoke_openrouter_with_schema
from src.lib.openrouter_client import call_openrouter
from src.lib.prompt_builder import build_brand_list_messages_batch
from src.lib.response_parser import parse_brand_list_batch_response

SKIP_RATIONALE = "Skipped: already is_about_brand=true"
VALID_CATEGORIES = {"listed_brand", "new_brand", "no_brand", "skipped"}


def skipped_result() -> Dict[str, Any]:
    return {
        "category": "skipped",
        "assigned_brand": "",
        "suggested_brand": "",
        "confidence": 0.0,
        "rationale": SKIP_RATIONALE,
    }


def merge_brand_list_output(row: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        **row,
        "category": result.get("category", "no_brand"),
        "assigned_brand": result.get("assigned_brand", ""),
        "suggested_brand": result.get("suggested_brand", ""),
        "confidence": result.get("confidence", 0.0),
        "rationale": result.get("rationale", "Missing classification result"),
    }


def _normalize_category_result(result: Dict[str, Any], brand_set: set[str]) -> Dict[str, Any]:
    category = str(result.get("category", "no_brand"))
    assigned_brand = str(result.get("assigned_brand", "") or "")
    suggested_brand = str(result.get("suggested_brand", "") or "")
    confidence = float(result.get("confidence", 0.0) or 0.0)
    rationale = str(result.get("rationale", "") or "").strip() or "Missing classification result"

    if category not in VALID_CATEGORIES:
        category = "no_brand"
        assigned_brand = ""
        suggested_brand = ""

    if category == "listed_brand":
        if assigned_brand.lower() not in brand_set:
            category = "no_brand"
            assigned_brand = ""
            suggested_brand = ""
    elif category == "new_brand":
        assigned_brand = ""
        if not suggested_brand.strip():
            category = "no_brand"
            suggested_brand = ""
    elif category == "no_brand":
        assigned_brand = ""
        suggested_brand = ""
    elif category == "skipped":
        return skipped_result()

    return {
        "category": category,
        "assigned_brand": assigned_brand,
        "suggested_brand": suggested_brand,
        "confidence": max(0.0, min(confidence, 1.0)),
        "rationale": rationale,
    }


def classify_brand_list_batch(
    rows: List[Dict[str, Any]],
    candidate_brands: List[str],
    model: str,
    api_key: str,
    client: Callable[[str, str, list, int, Dict[str, Any] | None, list | None], Dict[str, Any]] = call_openrouter,
) -> List[Dict[str, Any]]:
    if not rows:
        return []

    brand_set = {brand.lower() for brand in candidate_brands}
    messages = build_brand_list_messages_batch(rows, candidate_brands)
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "brand_list_classification",
            "schema": {
                "type": "object",
                "properties": {
                    "results": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "category": {
                                    "type": "string",
                                    "enum": ["listed_brand", "new_brand", "no_brand"],
                                },
                                "assigned_brand": {"type": "string"},
                                "suggested_brand": {"type": "string"},
                                "confidence": {"type": "number"},
                                "rationale": {"type": "string"},
                            },
                            "required": ["id", "category", "confidence", "rationale"],
                        },
                    }
                },
                "required": ["results"],
            },
        },
    }
    content = invoke_openrouter_with_schema(
        api_key,
        model,
        messages,
        response_format,
        client,
    )

    parsed = parse_brand_list_batch_response(content)
    by_id = {item["id"]: item for item in parsed}

    normalized: List[Dict[str, Any]] = []
    for idx in range(1, len(rows) + 1):
        item = by_id.get(idx)
        if not item:
            normalized.append(
                {
                    "category": "no_brand",
                    "assigned_brand": "",
                    "suggested_brand": "",
                    "confidence": 0.0,
                    "rationale": "Missing classification result",
                }
            )
            continue
        normalized.append(_normalize_category_result(item, brand_set))

    return normalized
