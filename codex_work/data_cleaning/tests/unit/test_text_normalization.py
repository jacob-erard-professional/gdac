import pandas as pd

from src.text.normalize_text import apply_text_normalization


def test_text_normalization_nfkc_whitespace():
    df = pd.DataFrame({"text": ["Hello\u00A0World  ", "  Foo\tBar"]})
    out = apply_text_normalization(df, "none")
    assert out["text_normalized"].tolist() == ["Hello World", "Foo Bar"]


def test_text_normalization_casing():
    df = pd.DataFrame({"text": ["MiXeD"]})
    out = apply_text_normalization(df, "lower")
    assert out["text_normalized"].tolist() == ["mixed"]
