import json
from pathlib import Path

from src.agents import brand_grouping_agent as brand_agent
from src.agents import parent_company_grouping_agent as parent_agent
from src.agents.rate_limit_policy import (
    MIN_INITIAL_BACKOFF_SECONDS,
    MIN_MAX_RATE_LIMIT_RETRIES,
    MIN_REQUEST_DELAY_SECONDS,
    enforce_rate_limit_policy,
)


def test_enforce_rate_limit_policy_clamps_low_values():
    request_delay, retries, backoff = enforce_rate_limit_policy(
        request_delay_seconds=0.0,
        max_rate_limit_retries=0,
        initial_backoff_seconds=0.1,
    )

    assert request_delay == MIN_REQUEST_DELAY_SECONDS
    assert retries == MIN_MAX_RATE_LIMIT_RETRIES
    assert backoff == MIN_INITIAL_BACKOFF_SECONDS


def test_brand_grouping_enforces_policy_for_invoker(monkeypatch, tmp_path: Path):
    in_path = tmp_path / "hashtags_frequency.json"
    out_path = tmp_path / "brand_groups.json"
    in_path.write_text(
        json.dumps({"year": "2024", "hashtags": [{"hashtag": "nfl", "count": 5}]}),
        encoding="utf-8",
    )

    captured = {}

    class DummyChat:
        def __init__(self, *args, **kwargs):
            return None

    class DummyInvoker:
        def __init__(self, llm, min_interval_seconds, max_rate_limit_retries, initial_backoff_seconds):
            captured["min_interval_seconds"] = min_interval_seconds
            captured["max_rate_limit_retries"] = max_rate_limit_retries
            captured["initial_backoff_seconds"] = initial_backoff_seconds

    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setattr(brand_agent, "ChatOpenAI", DummyChat)
    monkeypatch.setattr(brand_agent, "_RateLimitedInvoker", DummyInvoker)
    monkeypatch.setattr(
        brand_agent,
        "_map_chunk_to_brands",
        lambda _invoker, chunk: {item.hashtag: item.hashtag for item in chunk},
    )
    monkeypatch.setattr(
        brand_agent,
        "_normalize_brand_labels",
        lambda _invoker, labels: {label: label for label in labels},
    )

    brand_agent.run_brand_grouping(
        hashtags_path=in_path,
        output_path=out_path,
        request_delay_seconds=0.0,
        max_rate_limit_retries=0,
        initial_backoff_seconds=0.1,
    )

    assert captured["min_interval_seconds"] == MIN_REQUEST_DELAY_SECONDS
    assert captured["max_rate_limit_retries"] == MIN_MAX_RATE_LIMIT_RETRIES
    assert captured["initial_backoff_seconds"] == MIN_INITIAL_BACKOFF_SECONDS


def test_parent_grouping_enforces_policy_for_invoker(monkeypatch, tmp_path: Path):
    in_path = tmp_path / "brand_groups.json"
    out_path = tmp_path / "parent_company_groups.json"
    in_path.write_text(
        json.dumps(
            {
                "year": "2024",
                "brands": [{"brand": "nfl", "total_count": 5, "hashtags": [{"hashtag": "nfl", "count": 5}]}],
            }
        ),
        encoding="utf-8",
    )

    captured = {}

    class DummyChat:
        def __init__(self, *args, **kwargs):
            return None

    class DummyInvoker:
        def __init__(self, llm, min_interval_seconds, max_rate_limit_retries, initial_backoff_seconds):
            captured["min_interval_seconds"] = min_interval_seconds
            captured["max_rate_limit_retries"] = max_rate_limit_retries
            captured["initial_backoff_seconds"] = initial_backoff_seconds

    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setattr(parent_agent, "ChatOpenAI", DummyChat)
    monkeypatch.setattr(parent_agent, "_RateLimitedInvoker", DummyInvoker)
    monkeypatch.setattr(
        parent_agent,
        "_map_chunk_to_parent_companies",
        lambda _invoker, chunk: {item.brand: item.brand for item in chunk},
    )
    monkeypatch.setattr(
        parent_agent,
        "_normalize_parent_labels",
        lambda _invoker, labels: {label: label for label in labels},
    )

    parent_agent.run_parent_company_grouping(
        brand_groups_path=in_path,
        output_path=out_path,
        request_delay_seconds=0.0,
        max_rate_limit_retries=0,
        initial_backoff_seconds=0.1,
    )

    assert captured["min_interval_seconds"] == MIN_REQUEST_DELAY_SECONDS
    assert captured["max_rate_limit_retries"] == MIN_MAX_RATE_LIMIT_RETRIES
    assert captured["initial_backoff_seconds"] == MIN_INITIAL_BACKOFF_SECONDS
