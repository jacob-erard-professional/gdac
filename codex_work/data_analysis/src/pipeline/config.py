from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class YearConfig:
    year: str
    raw_dir: Path
    processed_dir: Path
    enriched_dir: Path
    analytics_dir: Path


@dataclass(frozen=True)
class RunRequest:
    mode: str  # stage | full_year | full_all_years
    stage: Optional[str]
    year: Optional[str]
    data_dir: Optional[Path]
    deterministic: bool = True
    with_sentiment: bool = False
    sentiment_dry_run: bool = False
    sentiment_verbose: bool = False


def validate_year(year: str) -> str:
    if not (year and len(year) == 4 and year.isdigit()):
        raise ValueError("year must be YYYY")
    return year
