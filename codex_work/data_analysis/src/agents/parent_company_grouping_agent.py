import json
import os
import re
from json import JSONDecodeError
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from random import uniform
from time import perf_counter, sleep
from typing import Dict, Iterable, List, Set, Tuple

from langchain_openai import ChatOpenAI

from src.agents.rate_limit_policy import (
    MAX_BACKOFF_SECONDS,
    MIN_INITIAL_BACKOFF_SECONDS,
    MIN_MAX_RATE_LIMIT_RETRIES,
    MIN_REQUEST_DELAY_SECONDS,
    enforce_rate_limit_policy,
    wait_for_slot,
)


MODEL_DEFAULT = "openai/gpt-4.1-mini"
NORMALIZE_CHUNK_SIZE = 200
LLM_TIMEOUT_SECONDS = 180
DEFAULT_OVERRIDE_FILE = Path(__file__).resolve().parents[2] / "config" / "parent_company_overrides.json"


@dataclass(frozen=True)
class BrandGroup:
    brand: str
    total_count: int
    hashtags: List[Dict[str, int | str]]


class ModelJsonParseError(ValueError):
    def __init__(self, message: str, raw_text: str):
        super().__init__(message)
        self.raw_text = raw_text


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
                _log_provider_error(exc, attempt, self.max_rate_limit_retries)
                if attempt >= self.max_rate_limit_retries:
                    raise
                backoff = _next_backoff_seconds(self.initial_backoff_seconds, attempt, exc)
                sleep(backoff)


def _is_rate_limit_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "429" in msg or "rate limit" in msg or "rate-limited" in msg


def _log_provider_error(exc: Exception, attempt: int, max_retries: int) -> None:
    text = str(exc)
    lowered = text.lower()
    if "<html" in lowered or "<!doctype html" in lowered or "openrouter" in lowered:
        print(f"[openrouter] provider error (attempt {attempt + 1}/{max_retries + 1}): {text}")


def _next_backoff_seconds(initial_backoff_seconds: float, attempt: int, exc: Exception) -> float:
    msg = str(exc).lower()
    if "temporarily rate-limited upstream" in msg:
        base = min(initial_backoff_seconds * (2 ** attempt), 120.0)
    else:
        base = min(initial_backoff_seconds * (2 ** attempt), MAX_BACKOFF_SECONDS)
    return round(base + uniform(0.0, 0.25), 3)


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


def _normalize_override_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _load_parent_company_overrides(path: Path = DEFAULT_OVERRIDE_FILE) -> dict[str, str]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid parent override file format: {path}")
    out: dict[str, str] = {}
    for key, value in payload.items():
        norm_key = _normalize_override_key(str(key))
        norm_value = str(value).strip().lower()
        if norm_key and norm_value:
            out[norm_key] = norm_value
    return out


def _override_parent(brand: str, overrides: dict[str, str]) -> str | None:
    return overrides.get(_normalize_override_key(brand))


def _repair_json_via_model(invoker: _RateLimitedInvoker, raw_text: str) -> dict:
    repair_prompt = (
        "Fix this into valid JSON only. Do not add explanation. Preserve keys and values as much as possible.\n"
        f"raw={json.dumps(raw_text, ensure_ascii=True)}"
    )
    repaired = invoker.invoke(repair_prompt)
    return _extract_json(str(repaired.content))


def _invoke_json(invoker: _RateLimitedInvoker, prompt: str, retries: int = 2) -> dict:
    last_error: Exception | None = None
    last_text = ""
    for _ in range(retries + 1):
        response = invoker.invoke(prompt)
        text = str(response.content)
        last_text = text
        try:
            return _extract_json(text)
        except (JSONDecodeError, ValueError) as exc:
            last_error = exc
            try:
                return _repair_json_via_model(invoker, text)
            except (JSONDecodeError, ValueError):
                continue
    raise ModelJsonParseError(f"Model response could not be parsed as JSON: {last_error}", last_text) from last_error


def _append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _append_parse_failure(path: Path, *, phase: str, detail: str, raw_text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(f"phase={phase}\n")
        f.write(f"detail={detail}\n")
        f.write(raw_text)
        f.write("\n\n---\n\n")


def _load_partial_mappings(path: Path) -> Tuple[Dict[str, str], Set[int]]:
    mappings: Dict[str, str] = {}
    completed: Set[int] = set()
    if not path.exists():
        return mappings, completed
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        phase = str(payload.get("phase", ""))
        chunk_index = payload.get("chunk_index")
        if phase.startswith("map_chunk") and isinstance(chunk_index, int):
            completed.add(chunk_index)
        for item in payload.get("mappings", []):
            brand = str(item.get("brand", "")).strip().lower()
            parent = str(item.get("parent_company", "")).strip().lower()
            if brand:
                mappings[brand] = parent or brand
    return mappings, completed


def _prompt_for_model(current_model: str, *, context: str) -> str | None:
    prompt = (
        f"[group-parent-companies] {context}. Current model '{current_model}'.\n"
        "Enter a new OpenRouter model id to retry, or press Enter to fall back: "
    )
    try:
        value = input(prompt).strip()
    except EOFError:
        return None
    return value or None


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
    invoker: _RateLimitedInvoker, chunk: List[BrandGroup], hints: List[Dict[str, str]]
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
        "- use the provided hints when a brand matches or when hashtags clearly indicate a known brand owner.\n"
        "- if parent company is unknown, keep parent_company equal to the brand label.\n"
        "- never return markdown.\n\n"
        f"hints={json.dumps(hints, ensure_ascii=True)}\n"
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
    if not unique_labels:
        return {}

    total_chunks = (len(unique_labels) + NORMALIZE_CHUNK_SIZE - 1) // NORMALIZE_CHUNK_SIZE
    start_time = perf_counter()
    completed = 0
    out: Dict[str, str] = {}
    for i in range(0, len(unique_labels), NORMALIZE_CHUNK_SIZE):
        chunk = unique_labels[i : i + NORMALIZE_CHUNK_SIZE]
        chunk_index = i // NORMALIZE_CHUNK_SIZE + 1
        print(f"[group-parent-companies] normalize chunk {chunk_index} size={len(chunk)}")
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
            f"labels={json.dumps(chunk, ensure_ascii=True)}"
        )
        payload = _invoke_json(invoker, prompt)
        aliases = payload.get("aliases", [])
        for alias in aliases:
            label = str(alias.get("label", "")).strip().lower()
            canonical = str(alias.get("canonical", "")).strip().lower() or label
            if label:
                out[label] = canonical
        for label in chunk:
            out.setdefault(label, label)
        completed += 1
        elapsed = perf_counter() - start_time
        avg = elapsed / completed
        remaining = total_chunks - completed
        eta = avg * remaining
        print(f"[group-parent-companies] normalize progress {completed}/{total_chunks} eta={eta:.1f}s")

    second_pass_labels = sorted(set(out.values()))
    if len(second_pass_labels) > 1:
        total_chunks = (len(second_pass_labels) + NORMALIZE_CHUNK_SIZE - 1) // NORMALIZE_CHUNK_SIZE
        start_time = perf_counter()
        completed = 0
        second_pass: Dict[str, str] = {}
        for i in range(0, len(second_pass_labels), NORMALIZE_CHUNK_SIZE):
            chunk = second_pass_labels[i : i + NORMALIZE_CHUNK_SIZE]
            chunk_index = i // NORMALIZE_CHUNK_SIZE + 1
            print(f"[group-parent-companies] normalize second-pass chunk {chunk_index} size={len(chunk)}")
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
                f"labels={json.dumps(chunk, ensure_ascii=True)}"
            )
            payload = _invoke_json(invoker, prompt)
            aliases = payload.get("aliases", [])
            for alias in aliases:
                label = str(alias.get("label", "")).strip().lower()
                canonical = str(alias.get("canonical", "")).strip().lower() or label
                if label:
                    second_pass[label] = canonical
            for label in chunk:
                second_pass.setdefault(label, label)
            completed += 1
            elapsed = perf_counter() - start_time
            avg = elapsed / completed
            remaining = total_chunks - completed
            eta = avg * remaining
            print(f"[group-parent-companies] normalize second-pass progress {completed}/{total_chunks} eta={eta:.1f}s")
        out = {label: second_pass.get(canonical, canonical) for label, canonical in out.items()}

    return out


def run_parent_company_grouping(
    brand_groups_path: Path,
    output_path: Path,
    model: str = MODEL_DEFAULT,
    chunk_size: int = 40,
    request_delay_seconds: float = MIN_REQUEST_DELAY_SECONDS,
    max_rate_limit_retries: int = MIN_MAX_RATE_LIMIT_RETRIES,
    initial_backoff_seconds: float = MIN_INITIAL_BACKOFF_SECONDS,
    resume: bool = True,
    hints_path: Path | None = None,
) -> Path:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is required in your environment")

    request_delay_seconds, max_rate_limit_retries, initial_backoff_seconds = enforce_rate_limit_policy(
        request_delay_seconds=request_delay_seconds,
        max_rate_limit_retries=max_rate_limit_retries,
        initial_backoff_seconds=initial_backoff_seconds,
    )
    parent_overrides = _load_parent_company_overrides()

    year, groups = _load_brand_groups(brand_groups_path)
    hints: List[Dict[str, str]] = []
    resolved_hints = hints_path
    if resolved_hints is None:
        resolved_hints = brand_groups_path.parents[2] / "config" / "parent_company_hints.json"
    if resolved_hints and not resolved_hints.is_absolute():
        resolved_hints = (brand_groups_path.parents[2] / resolved_hints).resolve()
    if resolved_hints and resolved_hints.exists():
        payload = json.loads(resolved_hints.read_text(encoding="utf-8"))
        hints = payload.get("hints", [])
    def _build_invoker(model_id: str) -> _RateLimitedInvoker:
        llm = ChatOpenAI(
            model=model_id,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0,
            max_retries=3,
            request_timeout=LLM_TIMEOUT_SECONDS,
        )
        return _RateLimitedInvoker(
            llm=llm,
            min_interval_seconds=request_delay_seconds,
            max_rate_limit_retries=max_rate_limit_retries,
            initial_backoff_seconds=initial_backoff_seconds,
        )

    current_model = model
    invoker = _build_invoker(current_model)
    aux_dir = output_path.parent.parent.parent / "aux" / output_path.parent.name
    partial_jsonl_path = aux_dir / f"{output_path.stem}_partial.jsonl"
    parse_failures_path = aux_dir / f"{output_path.stem}_parse_failures.txt"
    if not resume:
        for path in (partial_jsonl_path, parse_failures_path):
            if path.exists():
                path.unlink()

    brand_to_parent, completed_chunks = _load_partial_mappings(partial_jsonl_path) if resume else ({}, set())
    degraded_rate_limit_fallback = False
    degraded_parse_fallback = False
    for chunk_index, chunk in enumerate(_chunks(groups, size=chunk_size), start=1):
        if resume and chunk_index in completed_chunks:
            continue
        print(f"[group-parent-companies] mapping chunk {chunk_index} size={len(chunk)}")
        unresolved_chunk: List[BrandGroup] = []
        override_mappings = []
        for item in chunk:
            forced_parent = _override_parent(item.brand, parent_overrides)
            if forced_parent:
                brand_to_parent[item.brand] = forced_parent
                override_mappings.append({"brand": item.brand, "parent_company": forced_parent})
            else:
                unresolved_chunk.append(item)
        if override_mappings:
            _append_jsonl(
                partial_jsonl_path,
                {
                    "phase": "map_chunk_override",
                    "chunk_index": chunk_index,
                    "mappings": override_mappings,
                },
            )
        if not unresolved_chunk:
            continue

        attempt_model_switch = True
        while True:
            try:
                mapped = _map_chunk_to_parent_companies(invoker, unresolved_chunk, hints)
                brand_to_parent.update(mapped)
                _append_jsonl(
                    partial_jsonl_path,
                    {
                        "phase": "map_chunk",
                        "chunk_index": chunk_index,
                        "mappings": [
                            {"brand": item.brand, "parent_company": mapped.get(item.brand, item.brand)}
                            for item in unresolved_chunk
                        ],
                    },
                )
                break
            except ModelJsonParseError as exc:
                if attempt_model_switch:
                    new_model = _prompt_for_model(current_model, context="model response parse failed")
                    if new_model:
                        current_model = new_model
                        invoker = _build_invoker(current_model)
                        attempt_model_switch = False
                        continue
                degraded_parse_fallback = True
                _append_parse_failure(
                    parse_failures_path,
                    phase="map_chunk",
                    detail=str(exc),
                    raw_text=exc.raw_text,
                )
                for item in chunk:
                    if item.brand in brand_to_parent:
                        continue
                    brand_to_parent[item.brand] = item.brand
                _append_jsonl(
                    partial_jsonl_path,
                    {
                        "phase": "map_chunk_fallback",
                        "chunk_index": chunk_index,
                        "mappings": [
                            {"brand": item.brand, "parent_company": brand_to_parent[item.brand]}
                            for item in unresolved_chunk
                        ],
                    },
                )
                break
            except Exception as exc:  # noqa: BLE001
                if not _is_rate_limit_error(exc):
                    raise
                if attempt_model_switch:
                    new_model = _prompt_for_model(current_model, context="rate limit reached")
                    if new_model:
                        current_model = new_model
                        invoker = _build_invoker(current_model)
                        attempt_model_switch = False
                        continue
                degraded_rate_limit_fallback = True
                for item in chunk:
                    if item.brand in brand_to_parent:
                        continue
                    brand_to_parent[item.brand] = item.brand
                _append_jsonl(
                    partial_jsonl_path,
                    {
                        "phase": "map_chunk_rate_limit_fallback",
                        "chunk_index": chunk_index,
                        "mappings": [
                            {"brand": item.brand, "parent_company": brand_to_parent[item.brand]}
                            for item in unresolved_chunk
                        ],
                    },
                )
                break

    attempt_model_switch = True
    while True:
        try:
            print(f"[group-parent-companies] normalizing labels total={len(set(brand_to_parent.values()))}")
            alias_map = _normalize_parent_labels(invoker, list(brand_to_parent.values()))
            _append_jsonl(
                partial_jsonl_path,
                {
                    "phase": "normalize_labels",
                    "aliases": [
                        {"label": label, "canonical": canonical} for label, canonical in sorted(alias_map.items())
                    ],
                },
            )
            break
        except ModelJsonParseError as exc:
            if attempt_model_switch:
                new_model = _prompt_for_model(current_model, context="normalize labels parse failed")
                if new_model:
                    current_model = new_model
                    invoker = _build_invoker(current_model)
                    attempt_model_switch = False
                    continue
            degraded_parse_fallback = True
            _append_parse_failure(
                parse_failures_path,
                phase="normalize_labels",
                detail=str(exc),
                raw_text=exc.raw_text,
            )
            alias_map = {label: label for label in brand_to_parent.values()}
            break
        except Exception as exc:  # noqa: BLE001
            if not _is_rate_limit_error(exc):
                raise
            if attempt_model_switch:
                new_model = _prompt_for_model(current_model, context="rate limit reached")
                if new_model:
                    current_model = new_model
                    invoker = _build_invoker(current_model)
                    attempt_model_switch = False
                    continue
            degraded_rate_limit_fallback = True
            alias_map = {label: label for label in brand_to_parent.values()}
            break

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
        "model": current_model,
        "degraded_rate_limit_fallback": degraded_rate_limit_fallback,
        "degraded_parse_fallback": degraded_parse_fallback,
        "partial_results_file": str(partial_jsonl_path),
        "parse_failures_file": str(parse_failures_path),
        "source_file": str(brand_groups_path),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "parent_companies": parent_companies,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return output_path
