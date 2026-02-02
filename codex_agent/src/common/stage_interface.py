from typing import Protocol

from src.common.schemas.run_context import RunContext


class Stage(Protocol):
    def run(self, input_ref: str, config: dict, context: RunContext) -> dict: ...
