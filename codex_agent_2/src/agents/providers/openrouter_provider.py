from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from collections import defaultdict

from src.agents.interfaces import AgentMetadata, HashtagNormalizerAgent


class OpenRouterHashtagNormalizerAgent(HashtagNormalizerAgent):
    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-oss-120b:free",
        base_url: str = "https://openrouter.ai/api/v1/chat/completions",
        timeout_seconds: int = 120,
        temperature: float = 0.0,
        seed: int = 0,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature
        self.seed = seed

    def _extract_json(self, content: str) -> dict:
        text = content.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?", "", text).strip()
            text = re.sub(r"```$", "", text).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                return json.loads(text[start : end + 1])
            raise

    def _call_openrouter(self, prompt: str) -> dict:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You group similar hashtags into equivalence classes. "
                        "Return only valid JSON."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "seed": self.seed,
        }

        req = urllib.request.Request(
            self.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://local-pipeline",
                "X-Title": "nlp-pipeline-hashtag-normalizer",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                raw = json.loads(response.read().decode("utf-8"))
                content = raw["choices"][0]["message"]["content"]
                return self._extract_json(content)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"OpenRouter request failed: {exc.code} {body}") from exc

    def _fallback_grouping(self, candidates: list[dict], iteration: int):
        grouped: dict[str, list[str]] = defaultdict(list)
        for candidate in candidates:
            raw = candidate["tag"]
            canonical = candidate.get("normalized_token", raw.lower())
            grouped[canonical].append(raw)

        classes = []
        mappings = []
        trace = []
        for idx, (canonical, members) in enumerate(grouped.items(), start=1):
            classes.append(
                {
                    "class_id": f"cls-{iteration}-{idx}",
                    "canonical_tag": canonical,
                    "members": sorted(set(members)),
                    "aggregate_confidence": 0.7,
                    "iteration": iteration,
                }
            )
            for member in members:
                mappings.append(
                    {
                        "mapping_id": f"map-{iteration}-{idx}-{member}",
                        "raw_tag": member,
                        "canonical_tag": canonical,
                        "confidence": 0.7,
                        "state": "draft",
                        "evidence": ["fallback grouping"],
                    }
                )
                trace.append({"raw_tag": member, "canonical_tag": canonical, "reason": "fallback grouping"})
        return classes, mappings, trace

    def normalize(self, candidates: list[dict], prior_mappings: list[dict] | None = None, iteration: int = 1):
        prompt = {
            "task": "group hashtag variants into equivalence classes",
            "rules": [
                "Group hashtags that refer to same entity/event/time variant.",
                "Prefer a clear canonical tag for each class.",
                "Include confidence 0..1 and rationale evidence.",
            ],
            "output_schema": {
                "equivalence_classes": [
                    {
                        "class_id": "string",
                        "canonical_tag": "string",
                        "members": ["string"],
                        "aggregate_confidence": "number",
                        "iteration": "number",
                    }
                ],
                "mappings": [
                    {
                        "mapping_id": "string",
                        "raw_tag": "string",
                        "canonical_tag": "string",
                        "confidence": "number",
                        "state": "draft",
                        "evidence": ["string"],
                    }
                ],
                "trace": [{"raw_tag": "string", "canonical_tag": "string", "reason": "string"}],
            },
            "iteration": iteration,
            "prior_mappings": prior_mappings or [],
            "candidates": candidates,
        }

        try:
            model_out = self._call_openrouter(json.dumps(prompt))
            classes = model_out.get("equivalence_classes", [])
            mappings = model_out.get("mappings", [])
            trace = model_out.get("trace", [])
            if not classes or not mappings:
                raise ValueError("Model output missing classes or mappings")
        except Exception:
            classes, mappings, trace = self._fallback_grouping(candidates, iteration)

        metadata = AgentMetadata(
            provider="openrouter",
            model=self.model,
            model_version="api-v1",
            temperature=self.temperature,
            seed=self.seed,
        )
        return classes, mappings, trace, metadata


def build_openrouter_agent_from_env(
    model: str = "openai/gpt-oss-120b:free",
    temperature: float = 0.0,
    seed: int = 0,
    timeout_seconds: int = 120,
) -> OpenRouterHashtagNormalizerAgent:
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is not set. Put it in .env.openrouter and rerun the stage."
        )
    return OpenRouterHashtagNormalizerAgent(
        api_key=api_key,
        model=model,
        temperature=temperature,
        seed=seed,
        timeout_seconds=timeout_seconds,
    )
