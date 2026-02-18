"""Pipeline module for config orchestration and execution."""

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
    with_ad_sentiment: bool = False
    sentiment_model: str = "finiteautomata/bertweet-base-sentiment-analysis"
    sentiment_batch_size: int = 64
    sentiment_dry_run: bool = False
    sentiment_allow_fallback: bool = False
    sentiment_device: str = "cuda"
    ad_sentiment_min_tweets: int = 1
    with_parent_company_sentiment: bool = False
    with_agentic_emotion: bool = False
    parent_company_sentiment_min_tweets: int = 1
    agentic_emotion_model: Optional[str] = None
    agentic_emotion_batch_size: int = 40
    agentic_emotion_dry_run: bool = False
    agentic_emotion_brand_filter: Optional[str] = None
    agentic_emotion_examples_per_emotion: int = 3
    clean_outputs: bool = False


def validate_year(year: str) -> str:
    if not (year and len(year) == 4 and year.isdigit()):
        raise ValueError("year must be YYYY")
    return year


def extract_base_year(year_or_partition: str) -> str:
    value = str(year_or_partition or "").strip()
    if value.endswith("_full"):
        value = value[:-5]
    return validate_year(value)
