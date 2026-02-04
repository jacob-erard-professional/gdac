"""Shared rate-limit guardrails for all agentic workflows.

These minima are constitution-aligned safety defaults and are enforced even when
callers provide lower values.
"""

from threading import Lock
from time import monotonic, sleep

MIN_REQUEST_DELAY_SECONDS = 2.5
MIN_MAX_RATE_LIMIT_RETRIES = 12
MIN_INITIAL_BACKOFF_SECONDS = 2.0
MAX_BACKOFF_SECONDS = 30.0

_RATE_LIMIT_LOCK = Lock()
_RATE_LIMIT_LAST_CALL_BY_SCOPE: dict[str, float] = {}


def enforce_rate_limit_policy(
    *,
    request_delay_seconds: float,
    max_rate_limit_retries: int,
    initial_backoff_seconds: float,
) -> tuple[float, int, float]:
    return (
        max(MIN_REQUEST_DELAY_SECONDS, float(request_delay_seconds)),
        max(MIN_MAX_RATE_LIMIT_RETRIES, int(max_rate_limit_retries)),
        max(MIN_INITIAL_BACKOFF_SECONDS, float(initial_backoff_seconds)),
    )


def wait_for_slot(*, scope: str, min_interval_seconds: float) -> None:
    interval = max(MIN_REQUEST_DELAY_SECONDS, float(min_interval_seconds))
    with _RATE_LIMIT_LOCK:
        last_call_at = _RATE_LIMIT_LAST_CALL_BY_SCOPE.get(scope, 0.0)
        now = monotonic()
        wait = interval - (now - last_call_at)
        if wait > 0:
            sleep(wait)
            now = monotonic()
        _RATE_LIMIT_LAST_CALL_BY_SCOPE[scope] = now
