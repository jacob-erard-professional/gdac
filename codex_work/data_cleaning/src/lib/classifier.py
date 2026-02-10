from __future__ import annotations

from typing import Any, Dict, Callable

from src.lib.prompt_builder import build_messages_batch, PROMPT_VERSION
from src.lib.response_parser import parse_batch_response
from src.models.schemas import ClassificationResult, TweetRecord, missing_required


def _extract_content(response: Dict[str, Any]) -> str:
    try:
        return response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("Unexpected OpenRouter response format") from exc


def classify_batch(
    tweets: list[TweetRecord],
    model: str,
    api_key: str,
    client: Callable[[str, str, list, int, Dict[str, Any] | None, list | None], Dict[str, Any]],
) -> list[ClassificationResult]:
    prepared: list[tuple[int, TweetRecord]] = []
    results: list[ClassificationResult] = []

    for idx, tweet in enumerate(tweets, start=1):
        if missing_required(tweet.text, tweet.brand):
            results.append(
                ClassificationResult(
                    is_about_brand=False,
                    confidence=0.0,
                    rationale="Missing text or brand",
                    prompt_version=PROMPT_VERSION,
                )
            )
        else:
            prepared.append((idx, tweet))

    if prepared:
        messages = build_messages_batch([t for _, t in prepared])
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "batch_classification",
                "schema": {
                    "type": "object",
                    "properties": {
                        "results": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer"},
                                    "is_about_brand": {"type": "boolean"},
                                    "confidence": {"type": "number"},
                                    "rationale": {"type": "string"},
                                },
                                "required": ["id", "is_about_brand", "confidence", "rationale"],
                            },
                        }
                    },
                    "required": ["results"],
                },
            },
        }
        plugins = [{"id": "response-healing"}]
        content = _extract_content(
            client(
                api_key,
                model,
                messages,
                30,
                response_format,
                plugins,
            )
        )
        batch_results = parse_batch_response(content)
        by_id = {item["id"]: item for item in batch_results}
        for idx, _tweet in prepared:
            item = by_id.get(idx)
            if not item or not item["rationale"]:
                results.append(
                    ClassificationResult(
                        is_about_brand=False,
                        confidence=0.0,
                        rationale="Missing classification result",
                        prompt_version=PROMPT_VERSION,
                    )
                )
            else:
                results.append(
                    ClassificationResult(
                        is_about_brand=item["is_about_brand"],
                        confidence=item["confidence"],
                        rationale=item["rationale"],
                        prompt_version=PROMPT_VERSION,
                    )
                )

    return results
