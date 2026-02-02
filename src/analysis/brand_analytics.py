from dataclasses import dataclass
from difflib import SequenceMatcher
import re


def _to_float(value: object) -> float:
    text = str(value).strip()
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def _norm_brand(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def _sim(a: str, b: str) -> float:
    return SequenceMatcher(a=a, b=b).ratio()


@dataclass(slots=True)
class BrandCluster:
    canonical_brand: str
    normalized_key: str
    aliases: set[str]
    retweet_count: float = 0.0
    like_count: float = 0.0
    total_interaction: float = 0.0


class BrandAggregator:
    def __init__(self, typo_similarity_threshold: float = 0.87) -> None:
        self.typo_similarity_threshold = typo_similarity_threshold
        self.clusters: list[BrandCluster] = []

    def update(self, rows: list[dict]) -> None:
        for row in rows:
            brand = str(row.get("brand_ad_name", "")).strip() or "UNKNOWN_AD"
            rt = _to_float(row.get("retweet_count", 0))
            likes = _to_float(row.get("like_count", 0))
            replies = _to_float(row.get("reply_count", 0))
            quotes = _to_float(row.get("quote_count", 0))
            total = rt + likes + replies + quotes
            cluster = self._find_or_create(brand)
            cluster.aliases.add(brand)
            cluster.retweet_count += rt
            cluster.like_count += likes
            cluster.total_interaction += total

    def _find_or_create(self, brand: str) -> BrandCluster:
        key = _norm_brand(brand)
        best: BrandCluster | None = None
        best_score = 0.0
        for c in self.clusters:
            score = _sim(key, c.normalized_key)
            if score > best_score:
                best_score = score
                best = c
        if best and best_score >= self.typo_similarity_threshold:
            return best
        cluster = BrandCluster(
            canonical_brand=brand,
            normalized_key=key,
            aliases={brand},
        )
        self.clusters.append(cluster)
        return cluster

    def finalize(self, top_n: int = 300) -> list[dict]:
        rows = []
        for c in self.clusters:
            rows.append(
                {
                    "canonical_brand": c.canonical_brand,
                    "aliases": sorted(c.aliases),
                    "retweet_count": round(c.retweet_count, 3),
                    "like_count": round(c.like_count, 3),
                    "total_interaction": round(c.total_interaction, 3),
                }
            )
        rows.sort(key=lambda r: (-r["total_interaction"], -r["like_count"], -r["retweet_count"]))
        for idx, row in enumerate(rows, start=1):
            row["rank_by_total_interaction"] = idx
        return rows[:top_n]

