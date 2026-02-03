from __future__ import annotations

import json
from pathlib import Path

from src.pipeline.stages.emotion_lexicon import run as run_lexicon
from src.pipeline.stages.emotion_ml import run as run_ml


def test_emotion_lexicon_generates_predictions(tmp_path: Path):
    source = tmp_path / "clean.jsonl"
    source.write_text('{"id": 1, "text": "I love this ad lol"}\n')
    out = tmp_path / "lexicon.json"

    result = run_lexicon([str(source)], [str(out)], {"enabled": True}, False)
    assert result["status"] == "succeeded"

    payload = json.loads(out.read_text())
    assert payload["predictions"][0]["emotion"] in {
        "joy",
        "surprise",
        "anger",
        "disgust",
        "excitement",
        "disappointment",
        "humorous",
    }


def test_emotion_ml_respects_enabled_flag(tmp_path: Path):
    source = tmp_path / "clean.jsonl"
    source.write_text('{"id": 1, "text": "Great ad!"}\n')
    out = tmp_path / "ml.json"

    skipped = run_ml([str(source)], [str(out)], {"enabled": False}, False)
    assert skipped["status"] == "skipped"

    result = run_ml([str(source)], [str(out)], {"enabled": True}, False)
    assert result["status"] == "succeeded"
    payload = json.loads(out.read_text())
    assert payload["metadata"]["approach"] == "machine_learning_naive_bayes"
