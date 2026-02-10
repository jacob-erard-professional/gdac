import pytest

from src.lib.response_parser import parse_response, parse_batch_response


def test_parse_response_valid_json():
    content = '{"is_about_brand": true, "confidence": 0.9, "rationale": "Mentions brand"}'
    result = parse_response(content)
    assert result.is_about_brand is True
    assert result.confidence == 0.9
    assert result.rationale == "Mentions brand"


def test_parse_response_embedded_json():
    content = "Answer: {\"is_about_brand\": false, \"confidence\": 0.2, \"rationale\": \"Unrelated\"}"
    result = parse_response(content)
    assert result.is_about_brand is False
    assert result.confidence == 0.2


def test_parse_response_requires_rationale():
    content = '{"is_about_brand": true, "confidence": 0.5, "rationale": ""}'
    with pytest.raises(ValueError):
        parse_response(content)


def test_parse_response_clamps_confidence():
    content = '{"is_about_brand": true, "confidence": 2.5, "rationale": "Ok"}'
    result = parse_response(content)
    assert result.confidence == 1.0


def test_parse_batch_response():
    content = '{"results":[{"id":1,"is_about_brand":true,"confidence":0.8,"rationale":"Match"}]}'
    results = parse_batch_response(content)
    assert results[0]["id"] == 1
    assert results[0]["is_about_brand"] is True
