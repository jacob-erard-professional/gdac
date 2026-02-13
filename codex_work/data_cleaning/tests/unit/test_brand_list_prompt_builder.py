from src.lib.prompt_builder import build_brand_list_messages_batch


def test_build_brand_list_messages_contains_brand_list_and_rows():
    rows = [
        {"text": "I love Nike shoes", "is_about_brand": "false", "username": "a"},
        {"text": "No brand here", "is_about_brand": "false", "username": "b"},
    ]
    brands = ["Nike", "Adidas"]
    messages = build_brand_list_messages_batch(rows, brands)

    assert messages[0]["role"] == "system"
    content = messages[1]["content"]
    assert "Nike" in content
    assert "Adidas" in content
    assert "I love Nike shoes" in content
    assert "No brand here" in content
