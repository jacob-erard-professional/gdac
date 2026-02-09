import json
import os
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


MODEL_DEFAULT = "openai/gpt-4.1"
NORMALIZE_CHUNK_SIZE = 200
LLM_TIMEOUT_SECONDS = 180


@dataclass(frozen=True)
class HashtagCount:
    hashtag: str
    count: int


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


def _count_parse_failure_blocks(path: Path) -> int:
    if not path.exists():
        return 0
    return path.read_text(encoding="utf-8").count("\n\n---\n\n")


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
            hashtag = str(item.get("hashtag", "")).strip().lower()
            brand = str(item.get("brand", "")).strip().lower()
            if hashtag:
                mappings[hashtag] = brand or hashtag
    return mappings, completed


def _prompt_for_model(current_model: str, *, context: str) -> str | None:
    prompt = (
        f"[group-brands] {context}. Current model '{current_model}'.\n"
        "Enter a new OpenRouter model id to retry, or press Enter to fall back: "
    )
    try:
        value = input(prompt).strip()
    except EOFError:
        return None
    return value or None


def _map_chunk_to_brands(
    invoker: _RateLimitedInvoker, chunk: List[HashtagCount], hints: List[Dict[str, str]]
) -> Dict[str, str]:
    items = [{"hashtag": item.hashtag, "count": item.count} for item in chunk]
    prompt = (
        "Group hashtags into coherent canonical groups.\n"
        "Output strict JSON only with schema:\n"
        '{"mappings":[{"hashtag":"<string>","brand":"<canonical group label>"}]}\n'
        "Rules:\n"
        "- brand values are lowercase short labels like dc, pepsi, nfl, or lisa.\n"
        "- if two hashtags refer to the same concept, use exactly the same brand label.\n"
        "- Consider spelling variants, typos, abbreviations, numerals, and aliases as referring to the same concept when appropriate.\n"
        "- every hashtag MUST map to a specific group label.\n"
        "- do NOT use a generic catch-all label like 'unassigned'.\n"
        "- if a hashtag has no close match, create a singleton group label for it.\n"
        "- use provided hints when a hashtag matches a known franchise/brand keyword.\n"
        "- map every hashtag exactly once.\n"
        "- never return markdown.\n\n"
        f"hints={json.dumps(hints, ensure_ascii=True)}\n"
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
    if not unique_labels:
        return {}

    total_chunks = (len(unique_labels) + NORMALIZE_CHUNK_SIZE - 1) // NORMALIZE_CHUNK_SIZE
    start_time = perf_counter()
    completed = 0
    out: Dict[str, str] = {}
    for i in range(0, len(unique_labels), NORMALIZE_CHUNK_SIZE):
        chunk = unique_labels[i : i + NORMALIZE_CHUNK_SIZE]
        chunk_index = i // NORMALIZE_CHUNK_SIZE + 1
        print(f"[group-brands] normalize chunk {chunk_index} size={len(chunk)}")
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
        print(f"[group-brands] normalize progress {completed}/{total_chunks} eta={eta:.1f}s")

    # Second pass to merge aliases across chunks.
    second_pass_labels = sorted(set(out.values()))
    if len(second_pass_labels) > 1:
        total_chunks = (len(second_pass_labels) + NORMALIZE_CHUNK_SIZE - 1) // NORMALIZE_CHUNK_SIZE
        start_time = perf_counter()
        completed = 0
        second_pass: Dict[str, str] = {}
        for i in range(0, len(second_pass_labels), NORMALIZE_CHUNK_SIZE):
            chunk = second_pass_labels[i : i + NORMALIZE_CHUNK_SIZE]
            chunk_index = i // NORMALIZE_CHUNK_SIZE + 1
            print(f"[group-brands] normalize second-pass chunk {chunk_index} size={len(chunk)}")
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
            print(f"[group-brands] normalize second-pass progress {completed}/{total_chunks} eta={eta:.1f}s")
        out = {label: second_pass.get(canonical, canonical) for label, canonical in out.items()}

    return out


def run_brand_grouping(
    hashtags_path: Path,
    output_path: Path,
    model: str,
    chunk_size: int = 60,
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

    year, hashtags = _load_hashtags(hashtags_path)
    hints: List[Dict[str, str]] = []
    resolved_hints = hints_path
    if resolved_hints is None:
        resolved_hints = hashtags_path.parents[2] / "config" / "brand_group_hints.json"
    if resolved_hints and not resolved_hints.is_absolute():
        resolved_hints = (hashtags_path.parents[2] / resolved_hints).resolve()
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

    hashtag_to_brand, completed_chunks = _load_partial_mappings(partial_jsonl_path) if resume else ({}, set())
    degraded_rate_limit_fallback = False
    degraded_parse_fallback = False
    for chunk_index, chunk in enumerate(_chunks(hashtags, size=chunk_size), start=1):
        if resume and chunk_index in completed_chunks:
            continue
        print(f"[group-brands] mapping chunk {chunk_index} size={len(chunk)}")
        attempt_model_switch = True
        while True:
            try:
                mapped = _map_chunk_to_brands(invoker, chunk, hints)
                hashtag_to_brand.update(mapped)
                _append_jsonl(
                    partial_jsonl_path,
                    {
                        "phase": "map_chunk",
                        "chunk_index": chunk_index,
                        "mappings": [
                            {"hashtag": item.hashtag, "brand": mapped.get(item.hashtag, item.hashtag)}
                            for item in chunk
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
                    hashtag_to_brand[item.hashtag] = item.hashtag
                _append_jsonl(
                    partial_jsonl_path,
                    {
                        "phase": "map_chunk_fallback",
                        "chunk_index": chunk_index,
                        "mappings": [{"hashtag": item.hashtag, "brand": item.hashtag} for item in chunk],
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
                    hashtag_to_brand[item.hashtag] = item.hashtag
                _append_jsonl(
                    partial_jsonl_path,
                    {
                        "phase": "map_chunk_rate_limit_fallback",
                        "chunk_index": chunk_index,
                        "mappings": [{"hashtag": item.hashtag, "brand": item.hashtag} for item in chunk],
                    },
                )
                break

    attempt_model_switch = True
    while True:
        try:
            print(f"[group-brands] normalizing labels total={len(set(hashtag_to_brand.values()))}")
            alias_map = _normalize_brand_labels(invoker, list(hashtag_to_brand.values()))
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
            alias_map = {label: label for label in hashtag_to_brand.values()}
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
            alias_map = {label: label for label in hashtag_to_brand.values()}
            break

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
        "model": current_model,
        "degraded_rate_limit_fallback": degraded_rate_limit_fallback,
        "degraded_parse_fallback": degraded_parse_fallback,
        "partial_results_file": str(partial_jsonl_path),
        "parse_failures_file": str(parse_failures_path),
        "source_file": str(hashtags_path),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "brands": brands,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    if degraded_rate_limit_fallback or degraded_parse_fallback:
        recovered_path = aux_dir / f"{output_path.stem}_recovered.json"
        recovered_payload = {
            "year": year,
            "model": model,
            "recovered_from_partial": True,
            "degraded_rate_limit_fallback": degraded_rate_limit_fallback,
            "degraded_parse_fallback": degraded_parse_fallback,
            "partial_results_file": str(partial_jsonl_path),
            "parse_failures_file": str(parse_failures_path),
            "parse_failure_blocks": _count_parse_failure_blocks(parse_failures_path),
            "source_file": str(hashtags_path),
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "brands": brands,
        }
        recovered_path.write_text(json.dumps(recovered_payload, indent=2), encoding="utf-8")
        print(f"[group-brands] auto-recovery output written to {recovered_path}")

    return output_path
