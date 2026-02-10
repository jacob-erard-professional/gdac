import pytest

from src.brand.agent_schemas import AgentOutput


def test_agent_output_abstain_rules():
    payload = {
        "input_id": "abc",
        "brand_relevant": False,
        "router_model_used": "m",
        "prompt_version": "p",
        "output_hash": "h",
        "abstain": True,
        "confidence": None,
        "explanation": None,
    }
    output = AgentOutput.model_validate(payload)
    assert output.abstain is True


def test_agent_output_abstain_rejects_confidence():
    payload = {
        "input_id": "abc",
        "brand_relevant": False,
        "router_model_used": "m",
        "prompt_version": "p",
        "output_hash": "h",
        "abstain": True,
        "confidence": 0.2,
        "explanation": None,
    }
    with pytest.raises(ValueError):
        AgentOutput.model_validate(payload)
