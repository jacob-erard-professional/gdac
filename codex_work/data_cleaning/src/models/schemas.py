from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class TweetRecord:
    text: str
    brand: str
    metadata: Dict[str, Any]
    annotations: List[Dict[str, Any]]
    mentions: List[Dict[str, Any]]
    hashtags: List[Dict[str, Any]]
    cashtags: List[Dict[str, Any]]
    urls: List[Dict[str, Any]]
    referenced_tweets: List[Dict[str, Any]]
    public_metrics: Dict[str, int]


@dataclass
class ClassificationResult:
    is_about_brand: bool
    confidence: float
    rationale: str
    prompt_version: Optional[str] = None


@dataclass
class BrandListClassificationResult:
    category: str
    assigned_brand: str
    suggested_brand: str
    confidence: float
    rationale: str


def normalize_text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def missing_required(text: str, brand: str) -> bool:
    return not text or not brand


def clamp_confidence(value: Any) -> float:
    try:
        val = float(value)
    except (TypeError, ValueError):
        return 0.0
    if val < 0:
        return 0.0
    if val > 1:
        return 1.0
    return val


def ensure_rationale(value: Any) -> str:
    rationale = "" if value is None else str(value).strip()
    return rationale
