from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


SCHEMA_VERSION = "1.0.0"
EMOTIONS = [
    "joy",
    "surprise",
    "anger",
    "disgust",
    "excitement",
    "disappointment",
    "humorous",
]

LEXICON = {
    "joy": {"happy", "joy", "love", "great", "wonderful", "delight", "glad", "pleased", "smile", "awesome"},
    "surprise": {"surprise", "unexpected", "wow", "shocked", "astonished", "suddenly", "unbelievable"},
    "anger": {"angry", "mad", "furious", "hate", "annoyed", "rage", "outraged", "frustrated"},
    "disgust": {"disgust", "gross", "awful", "nasty", "revolting", "terrible", "sickening"},
    "excitement": {"excited", "hyped", "thrilled", "pumped", "epic", "letsgo", "can't wait", "cant wait", "fire"},
    "disappointment": {"disappointed", "sad", "letdown", "underwhelming", "meh", "boring", "bad", "worse"},
    "humorous": {"funny", "hilarious", "lol", "lmao", "joke", "comedy", "laugh", "rofl"},
}

WORD_RE = re.compile(r"[a-zA-Z']+")


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in WORD_RE.findall(text)]


def _score(text: str) -> dict[str, int]:
    lower = text.lower()
    toks = _tokens(text)
    counts = Counter(toks)
    scores: dict[str, int] = {}
    for emotion, words in LEXICON.items():
        total = 0
        for w in words:
            if " " in w:
                total += 1 if w in lower else 0
            else:
                total += counts.get(w, 0)
        scores[emotion] = total
    return scores


def _pick_emotion(scores: dict[str, int], text: str) -> str:
    if max(scores.values()) > 0:
        return max(EMOTIONS, key=lambda e: (scores[e], -EMOTIONS.index(e)))
    lower = text.lower()
    if "!" in text:
        return "excitement"
    if any(tok in lower for tok in ["haha", "lol", "lmao"]):
        return "humorous"
    return "disappointment"


def run(input_paths: list[str], output_paths: list[str], config: dict, dry_run: bool) -> dict:
    source = Path(input_paths[0])
    target = Path(output_paths[0])
    enabled = bool(config.get("enabled", False)) if config else False

    if dry_run:
        return {
            "status": "dry_run",
            "reads": [str(source)],
            "writes": [str(target)],
            "schema_version": SCHEMA_VERSION,
        }
    if not enabled:
        return {
            "status": "skipped",
            "reason": "Set enabled: true in config to run lexicon emotion classification.",
            "schema_version": SCHEMA_VERSION,
        }

    predictions = []
    summary = Counter()

    if source.exists() and source.read_text().strip():
        for idx, line in enumerate(source.read_text().splitlines(), start=1):
            row = json.loads(line)
            text = row.get("text", "")
            scores = _score(text)
            emotion = _pick_emotion(scores, text)
            summary[emotion] += 1
            predictions.append(
                {
                    "row_id": row.get("id", idx),
                    "text": text,
                    "emotion": emotion,
                    "scores": scores,
                }
            )

    payload = {
        "metadata": {
            "approach": "lexicon",
            "emotions": EMOTIONS,
            "source_input": str(source),
            "total_rows": len(predictions),
        },
        "summary": dict(summary),
        "predictions": predictions,
    }

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2))
    return {
        "status": "succeeded",
        "outputs": [str(target)],
        "schema_version": SCHEMA_VERSION,
    }
