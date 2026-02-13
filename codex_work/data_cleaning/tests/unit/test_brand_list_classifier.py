import pytest

from src.lib.brand_list_classifier import (
    SKIP_RATIONALE,
    classify_brand_list_batch,
    merge_brand_list_output,
    skipped_result,
)
from src.lib.csv_io import is_true_like, load_brand_list_csv


def fake_client(api_key, model, messages, timeout=30, response_format=None, plugins=None):
    return {
        "choices": [
            {
                "message": {
                    "content": '{"results":[{"id":1,"category":"listed_brand","assigned_brand":"Nike","confidence":0.9,"rationale":"Mentions Nike"},{"id":2,"category":"new_brand","suggested_brand":"Patanjali","confidence":0.6,"rationale":"Mentions Patanjali"},{"id":3,"category":"no_brand","confidence":0.2,"rationale":"No clear brand"}]}'
                }
            }
        ]
    }


def test_classify_brand_list_batch_categories():
    rows = [
        {"text": "Nike launched a shoe", "is_about_brand": "false"},
        {"text": "Patanjali soap ad", "is_about_brand": "false"},
        {"text": "random post", "is_about_brand": "false"},
    ]
    results = classify_brand_list_batch(rows, ["Nike", "Adidas"], "openrouter/test", "key", fake_client)
    assert results[0]["category"] == "listed_brand"
    assert results[0]["assigned_brand"] == "Nike"
    assert results[1]["category"] == "new_brand"
    assert results[1]["assigned_brand"] == ""
    assert results[1]["suggested_brand"] == "Patanjali"
    assert results[2]["category"] == "no_brand"


def test_skipped_result_contract():
    result = skipped_result()
    assert result["category"] == "skipped"
    assert result["assigned_brand"] == ""
    assert result["suggested_brand"] == ""
    assert result["confidence"] == 0.0
    assert result["rationale"] == SKIP_RATIONALE


def test_merge_brand_list_output_fields():
    row = {"text": "t", "is_about_brand": "true"}
    output = merge_brand_list_output(row, skipped_result())
    assert output["text"] == "t"
    assert output["category"] == "skipped"


@pytest.mark.parametrize("value", [True, "true", "TRUE", "1", "yes", "y"])
def test_is_true_like_true_values(value):
    assert is_true_like(value) is True


@pytest.mark.parametrize("value", [False, "false", "0", "", None, "no"])
def test_is_true_like_false_values(value):
    assert is_true_like(value) is False


def test_load_brand_list_csv_header_validation(tmp_path):
    p = tmp_path / "brands.csv"
    p.write_text("brand\nNike\nAdidas\n", encoding="utf-8")
    assert load_brand_list_csv(str(p)) == ["Nike", "Adidas"]


def test_load_brand_list_csv_rejects_wrong_header(tmp_path):
    p = tmp_path / "brands.csv"
    p.write_text("name\nNike\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_brand_list_csv(str(p))
