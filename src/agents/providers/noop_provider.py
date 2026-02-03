from __future__ import annotations

from collections import defaultdict

from src.agents.interfaces import AgentMetadata, HashtagNormalizerAgent


class NoopHashtagNormalizerAgent(HashtagNormalizerAgent):
    def normalize(self, candidates: list[dict], prior_mappings: list[dict] | None = None, iteration: int = 1):
        grouped: dict[str, list[str]] = defaultdict(list)
        for candidate in candidates:
            raw = candidate["tag"]
            canonical = candidate.get("normalized_token", raw.lower())
            grouped[canonical].append(raw)

        classes = []
        mappings = []
        trace = []
        for idx, (canonical, members) in enumerate(grouped.items(), start=1):
            classes.append(
                {
                    "class_id": f"cls-{iteration}-{idx}",
                    "canonical_tag": canonical,
                    "members": sorted(set(members)),
                    "aggregate_confidence": 0.9,
                    "iteration": iteration,
                }
            )
            for member in members:
                mapping = {
                    "mapping_id": f"map-{iteration}-{idx}-{member}",
                    "raw_tag": member,
                    "canonical_tag": canonical,
                    "confidence": 0.9,
                    "state": "draft",
                    "evidence": ["heuristic: normalized_token grouping"],
                }
                mappings.append(mapping)
                trace.append({"raw_tag": member, "canonical_tag": canonical, "reason": "token normalization"})

        metadata = AgentMetadata(
            provider="noop",
            model="noop-normalizer",
            model_version="1.0",
            temperature=0.0,
            seed=0,
        )
        return classes, mappings, trace, metadata
