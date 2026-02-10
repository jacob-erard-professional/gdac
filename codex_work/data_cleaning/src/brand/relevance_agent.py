from __future__ import annotations

import hashlib
import json
from typing import Any, Dict

from src.brand.agent_schemas import AgentInput, AgentOutput


PROMPT_TEMPLATE_V1 = """You are a brand relevance classifier.
Return JSON only with fields: brand_relevant (boolean), confidence (0-1, optional), explanation (short, optional), abstain (boolean).
If uncertain or input insufficient, set abstain true and omit confidence.

Brand: {brand}
Text: {text}
"""


def prompt_version(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]


def current_prompt_hash() -> str:
    return prompt_version(PROMPT_TEMPLATE_V1)


def build_agent_input_payload(text_normalized: str, brand_normalized: str, brand_original: str, model: str, model_params: Dict[str, Any]) -> AgentInput:
    prompt_text = PROMPT_TEMPLATE_V1.format(brand=brand_normalized, text=text_normalized)
    pv = prompt_version(PROMPT_TEMPLATE_V1)
    stable_payload = {
        "text_normalized": text_normalized,
        "brand_normalized": brand_normalized,
        "brand_original": brand_original,
        "prompt_version": pv,
        "model": model,
        "router_model_params": model_params,
    }
    input_id = hashlib.sha256(
        json.dumps(stable_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return AgentInput(input_id=input_id, **stable_payload), prompt_text


def parse_agent_response(
    raw_content: str,
    input_id: str,
    model_used: str,
    prompt_version_value: str,
) -> AgentOutput:
    try:
        data = json.loads(raw_content)
        data["input_id"] = input_id
        data["router_model_used"] = model_used
        data["prompt_version"] = prompt_version_value
        data["output_hash"] = hashlib.sha256(
            json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return AgentOutput.model_validate(data)
    except Exception as exc:
        fallback = {
            "input_id": input_id,
            "brand_relevant": False,
            "router_model_used": model_used,
            "prompt_version": prompt_version_value,
            "output_hash": hashlib.sha256(raw_content.encode("utf-8")).hexdigest(),
            "abstain": True,
            "error": f"parse_error: {exc}",
        }
        return AgentOutput.model_validate(fallback)
