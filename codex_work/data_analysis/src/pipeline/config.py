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
    with_deep_sentiment: bool = False
    with_parent_company_sentiment: bool = False
    with_parent_company_deep_sentiment: bool = False
    deep_sentiment_model: str = "cardiffnlp/twitter-roberta-base-emotion-latest"
    deep_sentiment_batch_size: int = 64
    deep_sentiment_dry_run: bool = False
    deep_sentiment_label_map_file: Optional[Path] = None
    deep_sentiment_device: str = "cuda"
    parent_company_sentiment_min_tweets: int = 1
    parent_company_deep_sentiment_min_tweets: int = 1


def validate_year(year: str) -> str:
    if not (year and len(year) == 4 and year.isdigit()):
        raise ValueError("year must be YYYY")
    return year
