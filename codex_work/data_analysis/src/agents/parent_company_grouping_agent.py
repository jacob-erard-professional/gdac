import json
import os
from json import JSONDecodeError
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic, sleep
from typing import Dict, Iterable, List

from langchain_openai import ChatOpenAI


MODEL_DEFAULT = "openai/gpt-oss-120b:free"


@dataclass(frozen=True)
class BrandGroup:
    brand: str
    total_count: int
    hashtags: List[Dict[str, int | str]]


@dataclass
class _RateLimitedInvoker:
    llm: ChatOpenAI
    min_interval_seconds: float
    max_rate_limit_retries: int
    initial_backoff_seconds: float
    _last_call_at: float = 0.0

    def invoke(self, prompt: str):
        now = monotonic()
        wait = self.min_interval_seconds - (now - self._last_call_at)
        if wait > 0:
            sleep(wait)

        for attempt in range(self.max_rate_limit_retries + 1):
            try:
                response = self.llm.invoke(prompt)
                self._last_call_at = monotonic()
                return response
            except Exception as exc:  # noqa: BLE001
                if not _is_rate_limit_error(exc):
                    raise
                if attempt >= self.max_rate_limit_retries:
                    raise
                backoff = min(self.initial_backoff_seconds * (2 ** attempt), 30.0)
                sleep(backoff)


def _is_rate_limit_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "429" in msg or "rate limit" in msg or "rate-limited" in msg


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


def _load_brand_groups(path: Path) -> tuple[str, List[BrandGroup]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    year = str(payload.get("year", "unknown"))
    raw_groups = payload.get("brands", [])

    groups: List[BrandGroup] = []
    for item in raw_groups:
        brand = str(item.get("brand", "")).strip().lower()
        if not brand:
            continue
        try:
            total_count = int(item.get("total_count", 0))
        except (TypeError, ValueError):
            total_count = 0
        hashtags = item.get("hashtags", [])
        if not isinstance(hashtags, list):
            hashtags = []
        groups.append(
            BrandGroup(
                brand=brand,
                total_count=max(total_count, 0),
                hashtags=hashtags,
            )
        )
    return year, groups


def _chunks(items: List[BrandGroup], size: int) -> Iterable[List[BrandGroup]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _map_chunk_to_parent_companies(
    invoker: _RateLimitedInvoker, chunk: List[BrandGroup]
) -> Dict[str, str]:
    items = [
        {
            "brand": item.brand,
            "total_count": item.total_count,
            "hashtags": [h.get("hashtag") for h in item.hashtags[:8] if isinstance(h, dict)],
        }
        for item in chunk
    ]
    prompt = (
        "Map each brand group to a real parent company label when known.\n"
        "Output strict JSON only with schema:\n"
        '{"mappings":[{"brand":"<string>","parent_company":"<canonical parent company label>"}]}\n'
        "Rules:\n"
        "- parent_company labels must be lowercase concise names.\n"
        "- every brand must map exactly once.\n"
        "- if parent company is unknown, keep parent_company equal to the brand label.\n"
        "- never return markdown.\n\n"
        f"brand_groups={json.dumps(items, ensure_ascii=True)}"
    )
    payload = _invoke_json(invoker, prompt)
    mappings = payload.get("mappings", [])
    out: Dict[str, str] = {}
    for mapping in mappings:
        brand = str(mapping.get("brand", "")).strip().lower()
        parent = str(mapping.get("parent_company", "")).strip().lower() or brand
        if brand:
            out[brand] = parent
    for item in chunk:
        out.setdefault(item.brand, item.brand)
    return out


def _normalize_parent_labels(invoker: _RateLimitedInvoker, labels: List[str]) -> Dict[str, str]:
    unique_labels = sorted(set(labels))
    prompt = (
        "Normalize parent company aliases.\n"
        "Output strict JSON only with schema:\n"
        '{"aliases":[{"label":"<input label>","canonical":"<merged canonical label>"}]}\n'
        "Rules:\n"
        "- keep labels lowercase.\n"
        "- merge only labels that clearly refer to the same company.\n"
        "- if unclear, keep label unchanged.\n"
        "- return one alias entry for every input label.\n"
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


def run_parent_company_grouping(
    brand_groups_path: Path,
    output_path: Path,
    model: str = MODEL_DEFAULT,
    chunk_size: int = 40,
    request_delay_seconds: float = 1.5,
    max_rate_limit_retries: int = 8,
    initial_backoff_seconds: float = 2.0,
) -> Path:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is required in your environment")

    year, groups = _load_brand_groups(brand_groups_path)
    llm = ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0,
        max_retries=3,
    )
    invoker = _RateLimitedInvoker(
        llm=llm,
        min_interval_seconds=max(0.0, request_delay_seconds),
        max_rate_limit_retries=max(0, max_rate_limit_retries),
        initial_backoff_seconds=max(0.5, initial_backoff_seconds),
    )

    brand_to_parent: Dict[str, str] = {}
    for chunk in _chunks(groups, size=chunk_size):
        brand_to_parent.update(_map_chunk_to_parent_companies(invoker, chunk))

    alias_map = _normalize_parent_labels(invoker, list(brand_to_parent.values()))

    grouped: Dict[str, List[dict]] = {}
    for group in groups:
        raw_parent = brand_to_parent.get(group.brand, group.brand)
        parent = alias_map.get(raw_parent, raw_parent)
        grouped.setdefault(parent, []).append(
            {
                "brand": group.brand,
                "total_count": group.total_count,
                "hashtags": group.hashtags,
            }
        )

    parent_companies = []
    for parent, children in grouped.items():
        ordered_children = sorted(
            children, key=lambda x: (-int(x["total_count"]), str(x["brand"]))
        )
        total = sum(int(c["total_count"]) for c in ordered_children)
        parent_companies.append(
            {
                "parent_company": parent,
                "total_count": total,
                "brands": ordered_children,
            }
        )
    parent_companies.sort(key=lambda x: (-int(x["total_count"]), str(x["parent_company"])))

    result = {
        "year": year,
        "model": model,
        "source_file": str(brand_groups_path),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "parent_companies": parent_companies,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return output_path
