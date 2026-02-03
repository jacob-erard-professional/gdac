from __future__ import annotations

from pathlib import Path


class DataResolutionError(ValueError):
    pass


def resolve_event_year_input(
    event: str,
    year: int,
    data_root: str = "data",
    file_name: str = "file.csv",
) -> str:
    event_dir = Path(data_root) / event / str(year)
    candidate = event_dir / file_name
    if candidate.exists():
        return str(candidate)

    csv_files = sorted(event_dir.glob("*.csv"))
    if len(csv_files) == 1:
        return str(csv_files[0])

    if len(csv_files) > 1:
        raise DataResolutionError(
            f"Multiple CSV files found in {event_dir}. Pass --file-name explicitly."
        )

    raise DataResolutionError(
        f"No input file found. Expected {candidate} or a single CSV under {event_dir}."
    )


def resolve_inputs(
    input_paths: list[str] | None,
    event: str | None,
    year: int | None,
    data_root: str,
    file_name: str,
) -> list[str]:
    if input_paths:
        return input_paths
    if event is None or year is None:
        raise DataResolutionError("Provide either --input or both --event and --year.")
    return [resolve_event_year_input(event, year, data_root=data_root, file_name=file_name)]
