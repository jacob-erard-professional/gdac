import json

from src.brand.relevance_agent import parse_agent_response


def test_parse_agent_response_invalid_json_abstains():
    output = parse_agent_response(
        raw_content="not json",
        input_id="abc",
        model_used="m",
        prompt_version_value="p",
    )
    assert output.abstain is True
    assert output.brand_relevant is False
    assert output.error


def test_parse_agent_response_valid_json():
    raw = json.dumps({"brand_relevant": True, "confidence": 0.9, "abstain": False})
    output = parse_agent_response(raw, "abc", "m", "p")
    assert output.brand_relevant is True
    assert output.abstain is False
