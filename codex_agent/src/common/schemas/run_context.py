from dataclasses import dataclass, asdict
from datetime import datetime, UTC


@dataclass(slots=True)
class RunContext:
    run_id: str
    event_name: str
    year: int
    config_path: str
    started_at: str

    @classmethod
    def create(cls, run_id: str, event_name: str, year: int, config_path: str) -> "RunContext":
        return cls(
            run_id=run_id,
            event_name=event_name,
            year=year,
            config_path=config_path,
            started_at=datetime.now(UTC).isoformat(),
        )

    def to_dict(self) -> dict:
        return asdict(self)
