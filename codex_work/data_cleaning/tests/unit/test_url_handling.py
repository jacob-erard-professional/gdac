import pandas as pd

from src.text.url_handling import apply_url_handling


def test_url_handling_replace():
    df = pd.DataFrame({"text_normalized": ["see https://example.com now"]})
    out = apply_url_handling(df, "replace", "[URL]")
    assert out["text_normalized"].tolist() == ["see [URL] now"]
    assert out["url_handling_applied"].all()


def test_url_handling_remove():
    df = pd.DataFrame({"text_normalized": ["see https://example.com now"]})
    out = apply_url_handling(df, "remove")
    assert out["text_normalized"].tolist() == ["see  now"]
