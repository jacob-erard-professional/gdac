from __future__ import annotations

import json
from typing import Any, Dict, List

from src.models.schemas import TweetRecord

PROMPT_VERSION = "v1"


def build_context(tweet: TweetRecord) -> Dict[str, Any]:
    return {
        "annotations": tweet.annotations,
        "mentions": tweet.mentions,
        "hashtags": tweet.hashtags,
        "cashtags": tweet.cashtags,
        "urls": tweet.urls,
        "referenced_tweets": tweet.referenced_tweets,
        "username": tweet.metadata.get("username"),
        "name": tweet.metadata.get("name"),
    }


def _toon_escape(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if any(ch in text for ch in [",", "\n", ":", "{", "}", "[", "]"]):
        return json.dumps(text, ensure_ascii=False)
    return text


def _json_compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def build_toon_batch(tweets: List[TweetRecord]) -> str:
    header = [
        "id",
        "brand",
        "text",
        "annotations",
        "mentions",
        "hashtags",
        "cashtags",
        "urls",
        "referenced_tweets",
        "username",
        "name",
    ]
    lines = ["tweets[%d]{%s}:" % (len(tweets), ",".join(header))]
    for idx, tweet in enumerate(tweets, start=1):
        context = build_context(tweet)
        row = [
            str(idx),
            _toon_escape(tweet.brand),
            _toon_escape(tweet.text),
            _toon_escape(_json_compact(context["annotations"])),
            _toon_escape(_json_compact(context["mentions"])),
            _toon_escape(_json_compact(context["hashtags"])),
            _toon_escape(_json_compact(context["cashtags"])),
            _toon_escape(_json_compact(context["urls"])),
            _toon_escape(_json_compact(context["referenced_tweets"])),
            _toon_escape(context["username"] or ""),
            _toon_escape(context["name"] or ""),
        ]
        lines.append(",".join(row))
    return "\n".join(lines)


def build_messages_batch(tweets: List[TweetRecord]) -> List[Dict[str, str]]:
    system = (
        "You are a strict classifier. Decide if each tweet is about the assigned brand. "
        "Use the tweet text as the primary signal. Use other fields only for "
        "disambiguation. Input is provided in TOON. Respond with JSON only."
    )
    toon_payload = build_toon_batch(tweets)
    user = (
        "Classify each tweet. Return JSON with a 'results' array of objects: "
        "{id, is_about_brand, confidence, rationale} where id matches the input row."
        "\n\nTOON INPUT:\n"
        f"{toon_payload}"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
