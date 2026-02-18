"""Tests for test parent company overrides behavior."""

import json
from pathlib import Path

import pytest

from src.agents import parent_company_grouping_agent as parent_agent


def test_parent_company_overrides_map_franchise_to_universal(monkeypatch, tmp_path: Path):
    in_path = tmp_path / "brand_groups.json"
    out_path = tmp_path / "parent_company_groups.json"
    in_path.write_text(
        json.dumps(
            {
                "year": "2024",
                "brands": [
                    {"brand": "despicableme4", "total_count": 10, "hashtags": [{"hashtag": "despicableme4", "count": 10}]},
                    {"brand": "minions", "total_count": 7, "hashtags": [{"hashtag": "minions", "count": 7}]},
                ],
            }
        ),
        encoding="utf-8",
    )

    class DummyChat:
        def __init__(self, *args, **kwargs):
            return None

    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setattr(parent_agent, "ChatOpenAI", DummyChat)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("LLM mapping should not be called when overrides cover all brands")

    monkeypatch.setattr(parent_agent, "_map_chunk_to_parent_companies", fail_if_called)
    monkeypatch.setattr(
        parent_agent,
        "_normalize_parent_labels",
        lambda _invoker, labels: {label: label for label in labels},
    )

    parent_agent.run_parent_company_grouping(
        brand_groups_path=in_path,
        output_path=out_path,
        model="openai/gpt-4.1",
        chunk_size=2,
    )

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    all_parents = {row["parent_company"] for row in payload["parent_companies"]}
    assert "universal" in all_parents

    universal_row = next(row for row in payload["parent_companies"] if row["parent_company"] == "universal")
    child_brands = {row["brand"] for row in universal_row["brands"]}
    assert {"despicableme4", "minions"}.issubset(child_brands)
