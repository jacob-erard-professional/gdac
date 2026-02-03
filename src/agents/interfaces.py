from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AgentMetadata:
    provider: str
    model: str
    model_version: str
    temperature: float
    seed: int


class HashtagNormalizerAgent:
    def normalize(
        self,
        candidates: list[dict],
        prior_mappings: list[dict] | None = None,
        iteration: int = 1,
    ) -> tuple[list[dict], list[dict], list[dict], AgentMetadata]:
        """Return (equivalence_classes, mappings, trace, metadata)."""
        raise NotImplementedError
