from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable, Dict


class AnalyticsModule(ABC):
    name: str

    @abstractmethod
    def run(self, rows: Iterable[Dict[str, str]], year: str, out_dir: Path) -> Path:
        raise NotImplementedError
