"""Tests for test analytics modules behavior."""

import json
from pathlib import Path
from src.analytics.registry import module_registry


def test_modules_produce_files(tmp_path: Path):
    rows = [
        {'hashtags': 'beta|alpha|alpha', 'text': 'hi @zed @amy @amy'},
        {'hashtags': 'beta', 'text': 'hello @amy @bob'},
    ]
    for name, fn in module_registry().items():
        out = fn(rows, '2024', tmp_path)
        assert out.exists(), name


def test_frequency_outputs_are_ranked(tmp_path: Path):
    rows = [
        {'hashtags': 'beta|alpha|alpha', 'text': 'hi @zed @amy @amy'},
        {'hashtags': 'beta', 'text': 'hello @amy @bob'},
    ]

    outputs = {}
    for name, fn in module_registry().items():
        outputs[name] = fn(rows, '2024', tmp_path)

    hashtags_payload = json.loads(outputs['hashtags_frequency'].read_text(encoding='utf-8'))
    mentions_payload = json.loads(outputs['mentions_frequency'].read_text(encoding='utf-8'))

    assert hashtags_payload['hashtags'] == [
        {'hashtag': 'alpha', 'count': 2},
        {'hashtag': 'beta', 'count': 2},
    ]
    assert mentions_payload['mentions'] == [
        {'mention': 'amy', 'count': 3},
        {'mention': 'bob', 'count': 1},
        {'mention': 'zed', 'count': 1},
    ]
