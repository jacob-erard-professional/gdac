from datetime import datetime, UTC
from .contracts import RunManifest


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def make_manifest(input_files, output_files, count_in, count_out, notes=None) -> RunManifest:
    started = utc_now()
    completed = utc_now()
    return RunManifest(
        input_files=[str(p) for p in input_files],
        output_files=[str(p) for p in output_files],
        record_counts={"input": int(count_in), "output": int(count_out)},
        started_at=started,
        completed_at=completed,
        notes=notes or [],
    )
