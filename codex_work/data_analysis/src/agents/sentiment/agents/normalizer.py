import re

from src.agents.sentiment.prompts import NORMALIZER_PROMPT
from src.agents.sentiment.schemas.agent_outputs import NormalizerOutput

URL_RE = re.compile(r"https?://\S+")
USER_RE = re.compile(r"@\w+")


def run_normalizer(text: str, llm_client=None) -> NormalizerOutput:
    if llm_client is None:
        removed_tokens = URL_RE.findall(text) + USER_RE.findall(text)
        cleaned = URL_RE.sub("", text)
        cleaned = USER_RE.sub("", cleaned)
        normalized = " ".join(cleaned.split())
        return NormalizerOutput(
            normalized_text=normalized,
            removed_tokens=removed_tokens,
            preserved_tokens=[],
            rationale="heuristic normalization",
        )

    payload = llm_client.invoke_json(f"{NORMALIZER_PROMPT}\ntext={text!r}")
    return NormalizerOutput.model_validate(payload)

