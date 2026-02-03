from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.agents.hashtag_normalizer import run_normalization_loop
from src.agents.providers.noop_provider import NoopHashtagNormalizerAgent
from src.agents.providers.openrouter_provider import build_openrouter_agent_from_env
from src.common.env import load_env_file
from src.artifacts.schemas.hashtag_normalization import HashtagNormalizationArtifact


SCHEMA_VERSION = "1.0.0"


def _prompt_hash(config: dict) -> str:
    material = json.dumps(config.get("prompt", {}), sort_keys=True).encode()
    return hashlib.sha256(material).hexdigest()


def run(input_paths: list[str], output_paths: list[str], config: dict, dry_run: bool) -> dict:
    source = Path(input_paths[0])
    target = Path(output_paths[0])
    iteration = int(config.get("iteration", 1)) if config else 1
    prior_path = Path(config.get("prior_mappings_path", "")) if config else None
    provider = str(config.get("provider", "noop")) if config else "noop"
    env_file = str(config.get("env_file", ".env.openrouter")) if config else ".env.openrouter"
    temperature = float(config.get("temperature", 0.0)) if config else 0.0
    seed = int(config.get("seed", 0)) if config else 0
    model = str(config.get("model", "openai/gpt-oss-120b:free")) if config else "openai/gpt-oss-120b:free"
    timeout_seconds = int(config.get("timeout_seconds", 120)) if config else 120

    if dry_run:
        return {"status": "dry_run", "reads": [str(source)], "writes": [str(target)], "schema_version": SCHEMA_VERSION}

    candidates = json.loads(source.read_text()) if source.exists() and source.read_text().strip() else []
    prior = None
    if prior_path and prior_path.exists() and prior_path.read_text().strip():
        prior_payload = json.loads(prior_path.read_text())
        prior = prior_payload.get("mappings", [])

    if provider == "openrouter":
        load_env_file(env_file)
        agent = build_openrouter_agent_from_env(
            model=model,
            temperature=temperature,
            seed=seed,
            timeout_seconds=timeout_seconds,
        )
    else:
        agent = NoopHashtagNormalizerAgent()

    classes, mappings, trace, metadata = run_normalization_loop(agent, candidates, iteration, prior)

    artifact = HashtagNormalizationArtifact(
        iteration=iteration,
        equivalence_classes=classes,
        mappings=mappings,
        trace=trace,
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(artifact.model_dump_json(indent=2))

    return {
        "status": "succeeded",
        "outputs": [str(target)],
        "schema_version": SCHEMA_VERSION,
        "determinism_mode": "non_deterministic",
        "model_provider": metadata["provider"],
        "model": metadata["model"],
        "model_version": metadata["model_version"],
        "temperature": metadata["temperature"],
        "seed": metadata["seed"],
        "prompt_hash": _prompt_hash(config or {}),
    }
