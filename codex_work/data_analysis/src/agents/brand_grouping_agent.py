import json
import os
from json import JSONDecodeError
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import sleep
from typing import Dict, Iterable, List

from langchain_openai import ChatOpenAI

from src.agents.rate_limit_policy import (
    MAX_BACKOFF_SECONDS,
    MIN_INITIAL_BACKOFF_SECONDS,
    MIN_MAX_RATE_LIMIT_RETRIES,
    MIN_REQUEST_DELAY_SECONDS,
    enforce_rate_limit_policy,
    wait_for_slot,
)


MODEL_DEFAULT = "openai/gpt-oss-120b:free"


@dataclass(frozen=True)
class HashtagCount:
    hashtag: str
    count: int


@dataclass
class _RateLimitedInvoker:
    llm: ChatOpenAI
    min_interval_seconds: float
    max_rate_limit_retries: int
    initial_backoff_seconds: float

    def invoke(self, prompt: str):
        wait_for_slot(scope="openrouter", min_interval_seconds=self.min_interval_seconds)

        for attempt in range(self.max_rate_limit_retries + 1):
            try:
                response = self.llm.invoke(prompt)
                return response
            except Exception as exc:  # noqa: BLE001
                if not _is_rate_limit_error(exc):
                    raise
                if attempt >= self.max_rate_limit_retries:
                    raise
                backoff = min(self.initial_backoff_seconds * (2 ** attempt), MAX_BACKOFF_SECONDS)
                sleep(backoff)


def _is_rate_limit_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "429" in msg or "rate limit" in msg or "rate-limited" in msg


def _load_hashtags(path: Path) -> tuple[str, List[HashtagCount]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    year = str(payload.get("year", "unknown"))
    raw_hashtags = payload.get("hashtags", [])

    if isinstance(raw_hashtags, dict):
        raw_hashtags = [
            {"hashtag": tag, "count": count} for tag, count in raw_hashtags.items()
        ]

    hashtags: List[HashtagCount] = []
    for item in raw_hashtags:
        tag = str(item.get("hashtag", "")).strip().lower()
        if not tag:
            continue
        try:
            count = int(item.get("count", 0))
        except (TypeError, ValueError):
            count = 0
        hashtags.append(HashtagCount(hashtag=tag, count=max(count, 0)))
    return year, hashtags


def _chunks(items: List[HashtagCount], size: int) -> Iterable[List[HashtagCount]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    if "```" in cleaned:
        cleaned = cleaned.replace("```json", "```")
        parts = [p.strip() for p in cleaned.split("```") if p.strip()]
        for part in parts:
            if part.startswith("{") and part.endswith("}"):
                return json.loads(part)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Model response did not contain valid JSON")
    return json.loads(cleaned[start : end + 1])


def _repair_json_via_model(invoker: _RateLimitedInvoker, raw_text: str) -> dict:
    repair_prompt = (
        "Fix this into valid JSON only. Do not add explanation. Preserve keys and values as much as possible.\n"
        f"raw={json.dumps(raw_text, ensure_ascii=True)}"
    )
    repaired = invoker.invoke(repair_prompt)
    return _extract_json(str(repaired.content))


def _invoke_json(invoker: _RateLimitedInvoker, prompt: str, retries: int = 2) -> dict:
    last_error: Exception | None = None
    for _ in range(retries + 1):
        response = invoker.invoke(prompt)
        text = str(response.content)
        try:
            return _extract_json(text)
        except (JSONDecodeError, ValueError) as exc:
            last_error = exc
            try:
                return _repair_json_via_model(invoker, text)
            except (JSONDecodeError, ValueError):
                continue
    raise ValueError(f"Model response could not be parsed as JSON: {last_error}") from last_error


def _map_chunk_to_brands(invoker: _RateLimitedInvoker, chunk: List[HashtagCount]) -> Dict[str, str]:
    items = [{"hashtag": item.hashtag, "count": item.count} for item in chunk]
    prompt = (
        "Group hashtags into coherent canonical groups.\n"
        "Output strict JSON only with schema:\n"
        '{"mappings":[{"hashtag":"<string>","brand":"<canonical group label>"}]}\n'
        "Rules:\n"
        "- brand values are lowercase short labels like dc, pepsi, nfl, or lisa.\n"
        "- if two hashtags refer to the same concept, use exactly the same brand label.\n"
        "- every hashtag MUST map to a specific group label.\n"
        "- do NOT use a generic catch-all label like 'unassigned'.\n"
        "- if a hashtag has no close match, create a singleton group label for it.\n"
        "- map every hashtag exactly once.\n"
        "- never return markdown.\n\n"
        f"hashtags={json.dumps(items, ensure_ascii=True)}"
    )
    payload = _invoke_json(invoker, prompt)
    mappings = payload.get("mappings", [])
    out: Dict[str, str] = {}
    for mapping in mappings:
        hashtag = str(mapping.get("hashtag", "")).strip().lower()
        brand = str(mapping.get("brand", "")).strip().lower() or hashtag
        if hashtag:
            out[hashtag] = brand
    for item in chunk:
        out.setdefault(item.hashtag, item.hashtag)
    return out


def _normalize_brand_labels(invoker: _RateLimitedInvoker, labels: List[str]) -> Dict[str, str]:
    unique_labels = sorted(set(labels))
    prompt = (
        "You will normalize brand label aliases.\n"
        "Output strict JSON only with schema:\n"
        '{"aliases":[{"label":"<input label>","canonical":"<merged canonical label>"}]}\n'
        "Rules:\n"
        "- Keep labels lowercase.\n"
        "- Only merge labels that clearly refer to the same brand/property.\n"
        "- Every label must resolve to a specific canonical group label.\n"
        "- Do NOT map labels to generic catch-alls like 'unassigned'.\n"
        "- If a label has no clear alias, keep it as its own canonical label.\n"
        "- Return one alias entry for every input label.\n"
        "- never return markdown.\n\n"
        f"labels={json.dumps(unique_labels, ensure_ascii=True)}"
    )
    payload = _invoke_json(invoker, prompt)
    aliases = payload.get("aliases", [])
    out: Dict[str, str] = {}
    for alias in aliases:
        label = str(alias.get("label", "")).strip().lower()
        canonical = str(alias.get("canonical", "")).strip().lower() or label
        if label:
            out[label] = canonical
    for label in unique_labels:
        out.setdefault(label, label)
    return out


def run_brand_grouping(
    hashtags_path: Path,
    output_path: Path,
    model: str = MODEL_DEFAULT,
    chunk_size: int = 60,
    request_delay_seconds: float = MIN_REQUEST_DELAY_SECONDS,
    max_rate_limit_retries: int = MIN_MAX_RATE_LIMIT_RETRIES,
    initial_backoff_seconds: float = MIN_INITIAL_BACKOFF_SECONDS,
) -> Path:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is required in your environment")

    request_delay_seconds, max_rate_limit_retries, initial_backoff_seconds = enforce_rate_limit_policy(
        request_delay_seconds=request_delay_seconds,
        max_rate_limit_retries=max_rate_limit_retries,
        initial_backoff_seconds=initial_backoff_seconds,
    )

    year, hashtags = _load_hashtags(hashtags_path)
    llm = ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0,
        max_retries=3,
    )
    invoker = _RateLimitedInvoker(
        llm=llm,
        min_interval_seconds=request_delay_seconds,
        max_rate_limit_retries=max_rate_limit_retries,
        initial_backoff_seconds=initial_backoff_seconds,
    )

    hashtag_to_brand: Dict[str, str] = {}
    for chunk in _chunks(hashtags, size=chunk_size):
        hashtag_to_brand.update(_map_chunk_to_brands(invoker, chunk))

    alias_map = _normalize_brand_labels(invoker, list(hashtag_to_brand.values()))

    grouped: Dict[str, List[Dict[str, int | str]]] = {}
    for item in hashtags:
        label = hashtag_to_brand.get(item.hashtag, item.hashtag)
        brand = alias_map.get(label, label)
        grouped.setdefault(brand, []).append(
            {"hashtag": item.hashtag, "count": item.count}
        )

    brands = []
    for brand, items in grouped.items():
        ordered_items = sorted(items, key=lambda x: (-int(x["count"]), str(x["hashtag"])))
        total = sum(int(i["count"]) for i in ordered_items)
        brands.append({"brand": brand, "total_count": total, "hashtags": ordered_items})
    brands.sort(key=lambda x: (-int(x["total_count"]), str(x["brand"])))

    result = {
        "year": year,
        "model": model,
        "source_file": str(hashtags_path),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "brands": brands,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return output_path
