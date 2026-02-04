from dataclasses import dataclass
import os


DEFAULT_MODEL = "openai/gpt-oss-120b:free"


@dataclass(frozen=True)
class AgentModelConfig:
    normalizer_model: str = DEFAULT_MODEL
    polarity_model: str = DEFAULT_MODEL
    emotion_model: str = DEFAULT_MODEL
    sarcasm_model: str = DEFAULT_MODEL
    supervisor_model: str = DEFAULT_MODEL


@dataclass(frozen=True)
class RuntimeConfig:
    request_delay_seconds: float = 1.0
    max_rate_limit_retries: int = 8
    initial_backoff_seconds: float = 2.0
    dry_run: bool = False
    verbose: bool = False


def get_openrouter_api_key(required: bool = True) -> str:
    key = os.getenv("OPENROUTER_API_KEY", "")
    if required and not key:
        raise ValueError("OPENROUTER_API_KEY is required in your environment")
    return key

