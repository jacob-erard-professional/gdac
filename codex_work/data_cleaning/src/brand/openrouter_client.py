from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


class OpenRouterClient:
    def __init__(self, api_base: str, api_key_env: str, timeout_seconds: int, max_retries: int):
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise ValueError(f"Missing OpenRouter API key in env var: {api_key_env}")
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _payload(
        self,
        prompt: str,
        model: str,
        model_params: Dict[str, Any],
        models: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a strict JSON generator."},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
        }
        if models:
            payload["models"] = models
        payload.update(model_params)
        return payload

    def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        with httpx.Client(timeout=self.timeout_seconds) as client:
            resp = client.post(
                f"{self.api_base}/chat/completions",
                headers=self._headers(),
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    def complete(self, prompt: str, model: str, model_params: Dict[str, Any], models: Optional[List[str]] = None) -> Dict[str, Any]:
        if self.max_retries <= 0:
            payload = self._payload(prompt, model, model_params, models)
            return self._post(payload)

        @retry(stop=stop_after_attempt(self.max_retries), wait=wait_exponential(min=1, max=10))
        def _retry_call() -> Dict[str, Any]:
            payload = self._payload(prompt, model, model_params, models)
            return self._post(payload)

        return _retry_call()
