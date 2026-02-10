from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from src.brand.openrouter_client import OpenRouterClient
from src.brand.relevance_agent import build_agent_input_payload, parse_agent_response, prompt_version


@dataclass
class AgentExecutionConfig:
    api_base: str
    api_key_env: str
    model: str
    models: Optional[List[str]]
    model_params: Dict[str, Any]
    timeout_seconds: int
    max_retries: int
    rate_limit_per_minute: int
    cost_ceiling_usd: float
    cost_per_call_usd: float
    batch_size: int


def _cache_path(cache_dir: Path, input_id: str) -> Path:
    return cache_dir / f"{input_id}.json"


def load_cached_output(cache_dir: Path, input_id: str) -> Optional[Dict[str, Any]]:
    path = _cache_path(cache_dir, input_id)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def store_cached_output(cache_dir: Path, input_id: str, payload: Dict[str, Any]) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = _cache_path(cache_dir, input_id)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _batched(rows: List[Tuple[str, str, str]], batch_size: int) -> Iterable[List[Tuple[str, str, str]]]:
    if batch_size <= 0:
        batch_size = 1
    for i in range(0, len(rows), batch_size):
        yield rows[i : i + batch_size]


def execute_brand_relevance(
    rows: Iterable[Tuple[str, str, str]],
    cache_dir: Path,
    config: AgentExecutionConfig,
) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
    client = OpenRouterClient(
        api_base=config.api_base,
        api_key_env=config.api_key_env,
        timeout_seconds=config.timeout_seconds,
        max_retries=config.max_retries,
    )
    outputs: List[Dict[str, Any]] = []
    cached_hits = 0
    calls_made = 0
    interval = 60.0 / max(config.rate_limit_per_minute, 1)
    spent = 0.0
    row_list = list(rows)
    for batch in _batched(row_list, config.batch_size):
        for text_normalized, brand_normalized, brand_original in batch:
            agent_input, prompt_text = build_agent_input_payload(
                text_normalized=text_normalized,
                brand_normalized=brand_normalized,
                brand_original=brand_original,
                model=config.model,
                model_params=config.model_params,
            )
            cached = load_cached_output(cache_dir, agent_input.input_id)
            if cached:
                outputs.append(cached)
                cached_hits += 1
                continue
            spent += config.cost_per_call_usd
            if spent > config.cost_ceiling_usd:
                raise RuntimeError("Cost ceiling exceeded during agent execution")
            calls_made += 1
            response = client.complete(
                prompt=prompt_text,
                model=config.model,
                model_params=config.model_params,
                models=config.models,
            )
            model_used = response.get("model", config.model)
            content = response["choices"][0]["message"]["content"]
            parsed = parse_agent_response(
                raw_content=content,
                input_id=agent_input.input_id,
                model_used=model_used,
                prompt_version_value=prompt_version(prompt_text),
            )
            payload = parsed.model_dump()
            store_cached_output(cache_dir, agent_input.input_id, payload)
            outputs.append(payload)
            time.sleep(interval)

    stats = {
        "calls_made": float(calls_made),
        "cached_hits": float(cached_hits),
        "estimated_cost_usd": float(spent),
    }
    return outputs, stats
