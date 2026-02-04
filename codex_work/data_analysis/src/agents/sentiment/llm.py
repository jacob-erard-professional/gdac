import json
from json import JSONDecodeError
from time import monotonic, sleep

from langchain_openai import ChatOpenAI


class OpenRouterJsonClient:
    def __init__(
        self,
        model: str,
        api_key: str,
        request_delay_seconds: float = 1.0,
        max_rate_limit_retries: int = 8,
        initial_backoff_seconds: float = 2.0,
    ):
        self._llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0,
            max_retries=3,
        )
        self._request_delay_seconds = max(0.0, request_delay_seconds)
        self._max_rate_limit_retries = max(0, max_rate_limit_retries)
        self._initial_backoff_seconds = max(0.5, initial_backoff_seconds)
        self._last_call_at = 0.0

    def invoke_json(self, prompt: str) -> dict:
        raw_text = self._invoke_with_retries(prompt)
        try:
            return self._extract_json(raw_text)
        except (JSONDecodeError, ValueError):
            repaired = self._invoke_with_retries(
                "Fix this into valid JSON only. Do not add explanation.\n"
                f"raw={json.dumps(raw_text, ensure_ascii=True)}"
            )
            return self._extract_json(repaired)

    def _invoke_with_retries(self, prompt: str) -> str:
        self._respect_rate_limit()
        for attempt in range(self._max_rate_limit_retries + 1):
            try:
                response = self._llm.invoke(prompt)
                self._last_call_at = monotonic()
                return str(response.content)
            except Exception as exc:  # noqa: BLE001
                if not self._is_rate_limit_error(exc):
                    raise
                if attempt >= self._max_rate_limit_retries:
                    raise
                backoff = min(self._initial_backoff_seconds * (2**attempt), 30.0)
                sleep(backoff)
        raise RuntimeError("LLM invocation failed unexpectedly")

    def _respect_rate_limit(self) -> None:
        now = monotonic()
        wait = self._request_delay_seconds - (now - self._last_call_at)
        if wait > 0:
            sleep(wait)

    @staticmethod
    def _is_rate_limit_error(exc: Exception) -> bool:
        msg = str(exc).lower()
        return "429" in msg or "rate limit" in msg or "rate-limited" in msg

    @staticmethod
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

