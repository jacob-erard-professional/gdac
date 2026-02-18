"""Agent workflow module for agentic emotion agent tasks."""

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from json import JSONDecodeError
from pathlib import Path
from random import uniform
from time import perf_counter, sleep
from typing import Any, Dict, Iterable, List, Tuple

import pandas as pd
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
LLM_TIMEOUT_SECONDS = 180
EMOTIONS = ["joy", "excitement", "anger", "disappointment", "frustration", "sadness"]
NEUTRAL_LABEL = "neutral"
PRESENCE_VALUES = {"emotional", "neutral", "uncertain"}
POLARITY_VALUES = {"positive", "negative", "neutral"}
SARCASM_VALUES = {"sarcastic", "not_sarcastic"}


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


def _prompt_for_model(current_model: str, *, context: str) -> str | None:
    prompt = (
        f"[agentic-emotion] {context}. Current model '{current_model}'.\n"
        "Enter a new OpenRouter model id to retry, or press Enter to fall back: "
    )
    try:
        value = input(prompt).strip()
    except EOFError:
        return None
    return value or None


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


def _load_partial_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    ids: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        for item in payload.get("records", []):
            row_id = str(item.get("row_id", "")).strip()
            if row_id:
                ids.add(row_id)
    return ids


def _seed_from_partial(
    path: Path,
    *,
    summary_counts: Dict[str, Dict[str, int]],
    example_pool: Dict[tuple[str, str], list[dict]],
    brand_filter: set[str] | None,
) -> int:
    if not path.exists():
        return 0
    total = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        for record in payload.get("records", []):
            brand = str(record.get("brand", "")).strip().lower()
            emotion = str(record.get("final_emotion", "")).strip().lower()
            if not brand or not emotion:
                continue
            if brand_filter and brand not in brand_filter:
                continue
            summary_counts.setdefault(brand, {})
            summary_counts[brand][emotion] = summary_counts[brand].get(emotion, 0) + 1
            total += 1
            if emotion != NEUTRAL_LABEL:
                example_pool.setdefault((brand, emotion), []).append(
                    {
                        "tweet_id": record.get("tweet_id", ""),
                        "text": record.get("text", ""),
                        "confidence": record.get("confidence", 0.0),
                        "username": record.get("username", ""),
                    }
                )
    return total


def _load_enriched_rows(path: Path, *, chunk_size: int) -> Iterable[pd.DataFrame]:
    return pd.read_csv(path, dtype=str, keep_default_na=False, chunksize=chunk_size)


def _row_id(row: dict) -> str:
    return str(row.get("pipeline_row_id") or row.get("tweet_id") or "").strip()


def _build_agent_prompt(task: str, schema: str, rules: list[str], items: list[dict]) -> str:
    return (
        f"{task}\n"
        "Output strict JSON only with schema:\n"
        f"{schema}\n"
        "Rules:\n"
        + "\n".join(f"- {rule}" for rule in rules)
        + "\n\n"
        f"tweets={json.dumps(items, ensure_ascii=True)}"
    )


def _presence_agent(invoker: _RateLimitedInvoker, items: list[dict]) -> Dict[str, dict]:
    prompt = _build_agent_prompt(
        "Determine if each tweet expresses strong emotion.",
        '{"decisions":[{"row_id":"<string>","presence":"emotional|neutral|uncertain","confidence":<float 0-1>"}]}',
        [
            "presence must be one of emotional, neutral, uncertain",
            "use neutral when no strong emotion is expressed",
            "be conservative; prefer neutral or uncertain over emotional",
            "return one decision per input row_id",
            "never return markdown",
        ],
        items,
    )
    payload = _invoke_json(invoker, prompt)
    out: Dict[str, dict] = {}
    for item in payload.get("decisions", []):
        row_id = str(item.get("row_id", "")).strip()
        presence = str(item.get("presence", "")).strip().lower()
        confidence = float(item.get("confidence", 0.0) or 0.0)
        if row_id:
            out[row_id] = {"presence": presence, "confidence": confidence}
    return out


def _polarity_agent(invoker: _RateLimitedInvoker, items: list[dict]) -> Dict[str, dict]:
    prompt = _build_agent_prompt(
        "Determine coarse sentiment polarity.",
        '{"decisions":[{"row_id":"<string>","polarity":"positive|negative|neutral","confidence":<float 0-1>"}]}',
        [
            "polarity must be one of positive, negative, neutral",
            "use neutral when polarity is unclear",
            "return one decision per input row_id",
            "never return markdown",
        ],
        items,
    )
    payload = _invoke_json(invoker, prompt)
    out: Dict[str, dict] = {}
    for item in payload.get("decisions", []):
        row_id = str(item.get("row_id", "")).strip()
        polarity = str(item.get("polarity", "")).strip().lower()
        confidence = float(item.get("confidence", 0.0) or 0.0)
        if row_id:
            out[row_id] = {"polarity": polarity, "confidence": confidence}
    return out


def _emotion_agent(invoker: _RateLimitedInvoker, items: list[dict]) -> Dict[str, dict]:
    prompt = _build_agent_prompt(
        "Assign a single dominant emotion.",
        '{"decisions":[{"row_id":"<string>","emotion":"<emotion>","confidence":<float 0-1>"}]}',
        [
            f"emotion must be one of {', '.join(EMOTIONS)}",
            "do NOT output neutral",
            "return one decision per input row_id",
            "never return markdown",
        ],
        items,
    )
    payload = _invoke_json(invoker, prompt)
    out: Dict[str, dict] = {}
    for item in payload.get("decisions", []):
        row_id = str(item.get("row_id", "")).strip()
        emotion = str(item.get("emotion", "")).strip().lower()
        confidence = float(item.get("confidence", 0.0) or 0.0)
        if row_id:
            out[row_id] = {"emotion": emotion, "confidence": confidence}
    return out


def _sarcasm_agent(invoker: _RateLimitedInvoker, items: list[dict]) -> Dict[str, dict]:
    prompt = _build_agent_prompt(
        "Detect sarcasm or irony.",
        '{"decisions":[{"row_id":"<string>","sarcasm":"sarcastic|not_sarcastic","confidence":<float 0-1>"}]}',
        [
            "sarcasm must be one of sarcastic, not_sarcastic",
            "be conservative; only mark sarcastic when clear",
            "return one decision per input row_id",
            "never return markdown",
        ],
        items,
    )
    payload = _invoke_json(invoker, prompt)
    out: Dict[str, dict] = {}
    for item in payload.get("decisions", []):
        row_id = str(item.get("row_id", "")).strip()
        sarcasm = str(item.get("sarcasm", "")).strip().lower()
        confidence = float(item.get("confidence", 0.0) or 0.0)
        if row_id:
            out[row_id] = {"sarcasm": sarcasm, "confidence": confidence}
    return out


def _polarity_for_emotion(emotion: str) -> str:
    if emotion in {"joy", "excitement"}:
        return "positive"
    if emotion in {"anger", "disappointment", "frustration", "sadness"}:
        return "negative"
    return "neutral"


def _supervise(
    *,
    presence: dict,
    polarity: dict,
    emotion: dict,
    sarcasm: dict,
) -> tuple[str, float]:
    presence_label = str(presence.get("presence", "")).lower()
    presence_conf = float(presence.get("confidence", 0.0))
    polarity_label = str(polarity.get("polarity", "")).lower()
    polarity_conf = float(polarity.get("confidence", 0.0))
    emotion_label = str(emotion.get("emotion", "")).lower()
    emotion_conf = float(emotion.get("confidence", 0.0))
    sarcasm_label = str(sarcasm.get("sarcasm", "")).lower()
    sarcasm_conf = float(sarcasm.get("confidence", 0.0))

    if presence_label not in PRESENCE_VALUES:
        presence_label = "uncertain"
    if polarity_label not in POLARITY_VALUES:
        polarity_label = "neutral"
    if sarcasm_label not in SARCASM_VALUES:
        sarcasm_label = "not_sarcastic"

    if presence_label != "emotional":
        base = presence_conf if presence_label == "neutral" else presence_conf * 0.6
        return NEUTRAL_LABEL, round(max(0.0, min(base, 1.0)), 4)

    if presence_conf < 0.6:
        return NEUTRAL_LABEL, round(presence_conf * 0.6, 4)

    if sarcasm_label == "sarcastic":
        return NEUTRAL_LABEL, round(min(presence_conf, sarcasm_conf) * 0.6, 4)

    if emotion_label not in EMOTIONS:
        return NEUTRAL_LABEL, round(min(presence_conf, emotion_conf) * 0.6, 4)

    required_polarity = _polarity_for_emotion(emotion_label)
    if polarity_label != required_polarity and polarity_conf >= 0.6:
        return NEUTRAL_LABEL, round(min(presence_conf, polarity_conf, emotion_conf) * 0.6, 4)

    confidence = min(presence_conf, polarity_conf, emotion_conf, sarcasm_conf)
    if polarity_conf < 0.6 or sarcasm_conf < 0.6:
        confidence *= 0.85
    return emotion_label, round(max(0.0, min(confidence, 1.0)), 4)


def run_agentic_emotion(
    *,
    year: int,
    enriched_path: Path,
    output_dir: Path,
    model: str,
    batch_size: int = 50,
    brand_filter: list[str] | None = None,
    dry_run: bool = False,
    request_delay_seconds: float = MIN_REQUEST_DELAY_SECONDS,
    max_rate_limit_retries: int = MIN_MAX_RATE_LIMIT_RETRIES,
    initial_backoff_seconds: float = MIN_INITIAL_BACKOFF_SECONDS,
    resume: bool = True,
    examples_per_emotion: int = 3,
) -> tuple[Path, Path]:
    if not enriched_path.exists():
        raise ValueError(f"Missing enriched input file: {enriched_path}")

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is required in your environment")

    request_delay_seconds, max_rate_limit_retries, initial_backoff_seconds = enforce_rate_limit_policy(
        request_delay_seconds=request_delay_seconds,
        max_rate_limit_retries=max_rate_limit_retries,
        initial_backoff_seconds=initial_backoff_seconds,
    )

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

    aux_dir = output_dir.parents[1] / "aux" / str(year)
    partial_path = aux_dir / "agentic_emotion_partial.jsonl"
    parse_failures_path = aux_dir / "agentic_emotion_parse_failures.txt"
    if not resume:
        for path in (partial_path, parse_failures_path):
            if path.exists():
                path.unlink()

    processed_ids = _load_partial_ids(partial_path) if resume else set()

    if dry_run:
        return output_dir / "agentic_emotion_summary.json", output_dir / "agentic_emotion_examples.json"

    invoker = _build_invoker(model)
    current_model = model

    brand_filter_set = {b.strip().lower() for b in (brand_filter or []) if b.strip()}
    summary_counts: Dict[str, Dict[str, int]] = {}
    example_pool: Dict[tuple[str, str], list[dict]] = {}
    total_rows = _seed_from_partial(
        partial_path,
        summary_counts=summary_counts,
        example_pool=example_pool,
        brand_filter=brand_filter_set or None,
    ) if resume else 0
    start_time = perf_counter()

    def _record_example(brand: str, emotion: str, record: dict) -> None:
        key = (brand, emotion)
        example_pool.setdefault(key, []).append(record)

    batch_items: list[dict] = []
    batch_meta: list[dict] = []

    def _flush_batch() -> None:
        nonlocal batch_items, batch_meta, current_model, invoker, total_rows
        if not batch_items:
            return
        attempt_model_switch = True
        while True:
            try:
                presence = _presence_agent(invoker, batch_items)
                polarity = _polarity_agent(invoker, batch_items)
                emotion = _emotion_agent(invoker, batch_items)
                sarcasm = _sarcasm_agent(invoker, batch_items)
                break
            except ModelJsonParseError as exc:
                if attempt_model_switch:
                    new_model = _prompt_for_model(current_model, context="model response parse failed")
                    if new_model:
                        current_model = new_model
                        invoker = _build_invoker(current_model)
                        attempt_model_switch = False
                        continue
                _append_parse_failure(parse_failures_path, phase="agentic_emotion", detail=str(exc), raw_text=exc.raw_text)
                presence = {}
                polarity = {}
                emotion = {}
                sarcasm = {}
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
                _append_parse_failure(parse_failures_path, phase="agentic_emotion_rate_limit", detail=str(exc), raw_text=str(exc))
                presence = {}
                polarity = {}
                emotion = {}
                sarcasm = {}
                break

        records = []
        for item, meta in zip(batch_items, batch_meta):
            row_id = item["row_id"]
            presence_row = presence.get(row_id, {"presence": "uncertain", "confidence": 0.0})
            polarity_row = polarity.get(row_id, {"polarity": "neutral", "confidence": 0.0})
            emotion_row = emotion.get(row_id, {"emotion": "", "confidence": 0.0})
            sarcasm_row = sarcasm.get(row_id, {"sarcasm": "not_sarcastic", "confidence": 0.0})
            final_emotion, final_conf = _supervise(
                presence=presence_row,
                polarity=polarity_row,
                emotion=emotion_row,
                sarcasm=sarcasm_row,
            )
            record = {
                "row_id": row_id,
                "tweet_id": meta["tweet_id"],
                "pipeline_row_id": meta["pipeline_row_id"],
                "brand": meta["brand"],
                "text": meta["text"],
                "username": meta["username"],
                "final_emotion": final_emotion,
                "confidence": final_conf,
                "agent_evidence": {
                    "emotion_presence": presence_row,
                    "polarity": polarity_row,
                    "emotion_candidate": emotion_row,
                    "sarcasm": sarcasm_row,
                },
            }
            records.append(record)

            brand = meta["brand"]
            summary_counts.setdefault(brand, {})
            summary_counts[brand][final_emotion] = summary_counts[brand].get(final_emotion, 0) + 1
            total_rows += 1

            if final_emotion != NEUTRAL_LABEL:
                _record_example(
                    brand,
                    final_emotion,
                    {
                        "tweet_id": meta["tweet_id"],
                        "text": meta["text"],
                        "confidence": final_conf,
                        "username": meta["username"],
                    },
                )

        _append_jsonl(
            partial_path,
            {
                "phase": "batch",
                "records": records,
            },
        )
        batch_items = []
        batch_meta = []

    for chunk in _load_enriched_rows(enriched_path, chunk_size=max(batch_size, 1) * 10):
        if "text" not in chunk.columns:
            raise ValueError("Enriched file missing required column: text")
        brand_col = "brand_tag" if "brand_tag" in chunk.columns else ("brand" if "brand" in chunk.columns else None)
        if brand_col is None:
            raise ValueError("Enriched file missing required column: brand_tag or brand")

        for _, row in chunk.iterrows():
            brand = str(row.get(brand_col, "")).strip().lower()
            if not brand:
                continue
            if brand_filter_set and brand not in brand_filter_set:
                continue
            tweet_id = str(row.get("id") or row.get("tweet_id") or "").strip()
            pipeline_row_id = str(row.get("pipeline_row_id", "")).strip()
            row_id = pipeline_row_id or tweet_id
            if not row_id or row_id in processed_ids:
                continue
            text = str(row.get("text", "")).strip()
            if not text:
                continue
            username = str(row.get("username", "")).strip()

            batch_items.append({"row_id": row_id, "text": text})
            batch_meta.append(
                {
                    "row_id": row_id,
                    "tweet_id": tweet_id,
                    "pipeline_row_id": pipeline_row_id,
                    "brand": brand,
                    "text": text,
                    "username": username,
                }
            )
            if len(batch_items) >= batch_size:
                print(f"[agentic-emotion] processing batch size={len(batch_items)}")
                _flush_batch()

    if batch_items:
        print(f"[agentic-emotion] processing batch size={len(batch_items)}")
        _flush_batch()

    summary_rows = []
    for brand in sorted(summary_counts.keys()):
        counts = summary_counts[brand]
        total = sum(counts.values())
        emotions = []
        for emotion in EMOTIONS + [NEUTRAL_LABEL]:
            count = counts.get(emotion, 0)
            emotions.append(
                {
                    "emotion": emotion,
                    "count": int(count),
                    "rate": round(count / total, 6) if total else 0.0,
                }
            )
        summary_rows.append(
            {
                "brand": brand,
                "tweet_count": int(total),
                "emotions": emotions,
            }
        )

    examples_rows = []
    for (brand, emotion), rows in sorted(example_pool.items()):
        if emotion == NEUTRAL_LABEL:
            continue
        top = sorted(rows, key=lambda r: (-float(r.get("confidence", 0.0)), r.get("tweet_id", "")))
        examples_rows.append(
            {
                "brand": brand,
                "emotion": emotion,
                "example_tweets": top[:examples_per_emotion],
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "agentic_emotion_summary.json"
    examples_path = output_dir / "agentic_emotion_examples.json"

    summary_payload = {
        "year": year,
        "total_rows": int(total_rows),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "brands": summary_rows,
    }
    summary_path.write_text(json.dumps(summary_payload, indent=2, sort_keys=True), encoding="utf-8")

    examples_payload = {
        "year": year,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "examples": examples_rows,
    }
    examples_path.write_text(json.dumps(examples_payload, indent=2, sort_keys=True), encoding="utf-8")

    elapsed = perf_counter() - start_time
    print(f"[agentic-emotion] complete rows={total_rows} elapsed={elapsed:.1f}s")

    return summary_path, examples_path
