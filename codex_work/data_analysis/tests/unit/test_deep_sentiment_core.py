from pathlib import Path

import pytest

from src.sentiment.deep_emotion import (
    ModelBundle,
    extract_hashtags,
    infer_deep_sentiment_batches,
    load_input_rows,
    preprocess_tweet_text,
    validate_label_mapping,
)


class _FakeTensor:
    def __init__(self, data):
        self.data = data

    def tolist(self):
        return self.data


class _FakeNoGrad:
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeTorch:
    @staticmethod
    def no_grad():
        return _FakeNoGrad()

    @staticmethod
    def softmax(logits, dim=-1):
        import math

        rows = logits.data
        probabilities = []
        for row in rows:
            exps = [math.exp(v) for v in row]
            total = sum(exps)
            probabilities.append([value / total for value in exps])
        return _FakeTensor(probabilities)

    @staticmethod
    def max(probabilities, dim=-1):
        max_values = []
        max_indices = []
        for row in probabilities.data:
            idx = max(range(len(row)), key=row.__getitem__)
            max_values.append(row[idx])
            max_indices.append(idx)
        return _FakeTensor(max_values), _FakeTensor(max_indices)


class _FakeTokenizer:
    def __call__(self, texts, **kwargs):
        return {"texts": texts, "kwargs": kwargs}


class _FakeModel:
    def __call__(self, **tokenized):
        texts = tokenized["texts"]
        logits = []
        for text in texts:
            if "joy" in text.lower():
                logits.append([0.1, 0.2, 0.3, 0.1, 1.5, 0.1])
            else:
                logits.append([0.1, 0.1, 1.8, 0.2, 0.1, 0.1])
        return type("Out", (), {"logits": _FakeTensor(logits)})()


def test_preprocess_removes_urls_and_normalizes_whitespace_only():
    text = "Wow   https://example.com   #SuperBowl  😄"
    processed = preprocess_tweet_text(text)
    assert processed == "Wow #SuperBowl 😄"


def test_extract_hashtags_is_deterministic_and_lowercased():
    text = "#GoTeam #Halftime #goteam"
    assert extract_hashtags(text) == ["goteam", "halftime"]


def test_validate_label_mapping_accepts_go_emotions_and_required_taxonomy():
    canonical = validate_label_mapping(
        {
            0: "anger",
            1: "disappointment",
            2: "neutral",
            3: "surprise",
            4: "joy",
            5: "excitement",
            6: "amusement",
        }
    )
    assert canonical[6] == "amusement"
    assert set(canonical.values()).issuperset(
        {"joy", "surprise", "anger", "disappointment", "excitement", "neutral"}
    )


def test_validate_label_mapping_accepts_unknown_labels_without_override():
    canonical = validate_label_mapping(
        {
            0: "anger",
            1: "disappointment",
            2: "neutral",
            3: "surprise",
            4: "joy",
            5: "excitement",
            6: "mystery",
        }
    )
    assert canonical[6] == "mystery"


def test_validate_label_mapping_accepts_override_for_unknown_labels():
    canonical = validate_label_mapping(
        {
            0: "anger",
            1: "disappointment",
            2: "neutral",
            3: "surprise",
            4: "joy",
            5: "mystery",
        },
        label_overrides={"mystery": "excitement"},
    )
    assert canonical[5] == "excitement"


def test_load_input_rows_supports_id_column_and_derives_hashtags(tmp_path: Path):
    input_path = tmp_path / "cleaned.csv"
    input_path.write_text(
        "id,text,created_at\n"
        "2,#Two second,2024-01-02 10:00:00\n"
        "1,#One first,2024-01-01 09:00:00\n",
        encoding="utf-8",
    )

    rows, invalid = load_input_rows(input_path, target_year=2024)

    assert invalid == 0
    assert [row["tweet_id"] for row in rows] == ["1", "2"]
    assert rows[0]["hashtags"] == ["one"]
    assert all(row["year"] == 2024 for row in rows)


def test_infer_deep_sentiment_batches_outputs_required_fields(monkeypatch):
    monkeypatch.setattr("src.sentiment.deep_emotion._require_dependencies", lambda: (_FakeTorch(), None, None))

    bundle = ModelBundle(
        model=_FakeModel(),
        tokenizer=_FakeTokenizer(),
        model_id="fake",
        id2label={0: "neutral", 1: "surprise", 2: "anger", 3: "disappointment", 4: "joy", 5: "excitement"},
        canonical_id2label={
            0: "neutral",
            1: "surprise",
            2: "anger",
            3: "disappointment",
            4: "joy",
            5: "excitement",
        },
        commit_hash=None,
    )

    records = infer_deep_sentiment_batches(
        [
            {"tweet_id": "1", "text": "pure joy", "hashtags": ["a"], "year": 2024},
            {"tweet_id": "2", "text": "so mad", "hashtags": ["b"], "year": 2024},
        ],
        model_bundle=bundle,
        batch_size=2,
        device="cpu",
    )

    assert records[0]["main_sentiment"] == "neutral"
    assert records[1]["main_sentiment"] == "neutral"
    assert set(records[0].keys()) >= {"tweet_id", "hashtags", "text", "main_sentiment"}
