from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path

from src.pipeline.stages.emotion_lexicon import EMOTIONS, LEXICON


SCHEMA_VERSION = "1.0.0"
WORD_RE = re.compile(r"[a-zA-Z']+")


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in WORD_RE.findall(text)]


def _weak_label(text: str) -> str | None:
    lower = text.lower()
    scores = {}
    toks = Counter(_tokens(text))
    for emotion, words in LEXICON.items():
        score = 0
        for w in words:
            if " " in w:
                score += 1 if w in lower else 0
            else:
                score += toks.get(w, 0)
        scores[emotion] = score
    top = max(EMOTIONS, key=lambda e: scores[e])
    return top if scores[top] > 0 else None


def _train_nb(samples: list[tuple[list[str], str]]):
    class_counts = Counter()
    token_counts = {emotion: Counter() for emotion in EMOTIONS}
    vocab = set()

    for tokens, label in samples:
        class_counts[label] += 1
        token_counts[label].update(tokens)
        vocab.update(tokens)

    if not vocab:
        vocab = {"__empty__"}

    total_docs = max(len(samples), 1)
    priors = {emotion: (class_counts[emotion] + 1) / (total_docs + len(EMOTIONS)) for emotion in EMOTIONS}

    likelihood = {}
    vocab_size = len(vocab)
    for emotion in EMOTIONS:
        total = sum(token_counts[emotion].values())
        likelihood[emotion] = {
            token: (token_counts[emotion][token] + 1) / (total + vocab_size)
            for token in vocab
        }
        likelihood[emotion]["__unk__"] = 1 / (total + vocab_size)

    return {
        "priors": priors,
        "likelihood": likelihood,
        "vocab": sorted(vocab),
        "class_counts": dict(class_counts),
        "train_rows": len(samples),
    }


def _predict(tokens: list[str], model: dict):
    log_probs = {}
    for emotion in EMOTIONS:
        logp = math.log(model["priors"][emotion])
        for tok in tokens:
            prob = model["likelihood"][emotion].get(tok, model["likelihood"][emotion]["__unk__"])
            logp += math.log(prob)
        log_probs[emotion] = logp

    max_log = max(log_probs.values())
    exps = {k: math.exp(v - max_log) for k, v in log_probs.items()}
    denom = sum(exps.values())
    probs = {k: exps[k] / denom for k in EMOTIONS}
    label = max(EMOTIONS, key=lambda e: probs[e])
    return label, probs


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
            "reason": "Set enabled: true in config to run ML emotion classification.",
            "schema_version": SCHEMA_VERSION,
        }

    rows = []
    if source.exists() and source.read_text().strip():
        for idx, line in enumerate(source.read_text().splitlines(), start=1):
            row = json.loads(line)
            rows.append({"row_id": row.get("id", idx), "text": row.get("text", "")})

    weak_samples: list[tuple[list[str], str]] = []
    for row in rows:
        label = _weak_label(row["text"])
        if label:
            weak_samples.append((_tokens(row["text"]), label))

    model = _train_nb(weak_samples)

    predictions = []
    summary = Counter()
    for row in rows:
        tokens = _tokens(row["text"])
        label, probs = _predict(tokens, model)
        summary[label] += 1
        predictions.append(
            {
                "row_id": row["row_id"],
                "text": row["text"],
                "emotion": label,
                "probabilities": probs,
            }
        )

    payload = {
        "metadata": {
            "approach": "machine_learning_naive_bayes",
            "emotions": EMOTIONS,
            "source_input": str(source),
            "total_rows": len(rows),
            "train_rows": model["train_rows"],
        },
        "model": {
            "class_counts": model["class_counts"],
            "vocab_size": len(model["vocab"]),
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
