from __future__ import annotations

from typing import Iterable

from networkx import DiGraph, is_directed_acyclic_graph
from pydantic import BaseModel, Field


class StageDefinition(BaseModel):
    name: str = Field(pattern=r"^[a-z][a-z0-9_-]{1,63}$")
    dependencies: list[str] = Field(default_factory=list)
    input_schema_versions: list[str] = Field(default_factory=lambda: ["1.0.0"])
    output_schema_versions: list[str] = Field(default_factory=lambda: ["1.0.0"])
    runner: str
    supports_dry_run: bool = True


STAGE_REGISTRY: dict[str, StageDefinition] = {
    "ingest": StageDefinition(name="ingest", dependencies=[], runner="src.pipeline.stages.ingest:run"),
    "clean": StageDefinition(name="clean", dependencies=["ingest"], runner="src.pipeline.stages.clean:run"),
    "enrich": StageDefinition(name="enrich", dependencies=["clean"], runner="src.pipeline.stages.enrich:run"),
    "analyze": StageDefinition(name="analyze", dependencies=["enrich"], runner="src.pipeline.stages.analyze:run"),
    "emotion-lexicon": StageDefinition(
        name="emotion-lexicon",
        dependencies=["clean"],
        runner="src.pipeline.stages.emotion_lexicon:run",
    ),
    "emotion-ml": StageDefinition(
        name="emotion-ml",
        dependencies=["clean"],
        runner="src.pipeline.stages.emotion_ml:run",
    ),
    "normalize-hashtags": StageDefinition(
        name="normalize-hashtags",
        dependencies=["enrich"],
        runner="src.pipeline.stages.normalize_hashtags:run",
    ),
}


class DependencyValidationError(ValueError):
    def __init__(self, missing: dict[str, list[str]]):
        super().__init__(f"Missing dependencies for selected stages: {missing}")
        self.missing = missing


class UnknownStageError(ValueError):
    pass


def validate_registry(registry: dict[str, StageDefinition] | None = None) -> None:
    registry = registry or STAGE_REGISTRY
    unknown_deps: dict[str, list[str]] = {}
    graph = DiGraph()

    for name, definition in registry.items():
        graph.add_node(name)
        for dep in definition.dependencies:
            if dep not in registry:
                unknown_deps.setdefault(name, []).append(dep)
            graph.add_edge(dep, name)

    if unknown_deps:
        raise UnknownStageError(f"Unknown dependencies found: {unknown_deps}")
    if not is_directed_acyclic_graph(graph):
        raise ValueError("Stage dependency graph contains a cycle")


def get_stage(name: str) -> StageDefinition:
    if name not in STAGE_REGISTRY:
        raise UnknownStageError(f"Unknown stage: {name}")
    return STAGE_REGISTRY[name]


def validate_selected_subset(selected_stages: Iterable[str]) -> None:
    selected = set(selected_stages)
    missing: dict[str, list[str]] = {}
    for stage in selected:
        definition = get_stage(stage)
        missing_deps = [dep for dep in definition.dependencies if dep not in selected]
        if missing_deps:
            missing[stage] = missing_deps
    if missing:
        raise DependencyValidationError(missing)
