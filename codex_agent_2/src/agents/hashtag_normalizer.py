from __future__ import annotations

from src.agents.interfaces import HashtagNormalizerAgent
from src.artifacts.schemas.hashtag_normalization import (
    EquivalenceClass,
    HashtagMapping,
)


def run_normalization_loop(
    agent: HashtagNormalizerAgent,
    candidates: list[dict],
    iteration: int,
    prior_mappings: list[dict] | None = None,
) -> tuple[list[dict], list[dict], list[dict], dict]:
    classes, mappings, trace, metadata = agent.normalize(
        candidates=candidates,
        prior_mappings=prior_mappings,
        iteration=iteration,
    )

    validated_classes = [EquivalenceClass.model_validate(item).model_dump() for item in classes]
    validated_mappings = []
    for item in mappings:
        item = dict(item)
        item.setdefault("agent_run_id", f"agent-{iteration}")
        validated_mappings.append(HashtagMapping.model_validate(item).model_dump(mode="json"))

    return (
        validated_classes,
        validated_mappings,
        trace,
        {
            "provider": metadata.provider,
            "model": metadata.model,
            "model_version": metadata.model_version,
            "temperature": metadata.temperature,
            "seed": metadata.seed,
        },
    )
