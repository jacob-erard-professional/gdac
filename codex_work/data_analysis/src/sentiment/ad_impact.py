import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.pipeline.stage_runtime import make_manifest

REQUIRED_SENTIMENT_COLUMNS = {"tweet_id", "year", "sentiment", "confidence", "text"}
REQUIRED_ENRICHED_COLUMNS = {"id", "ad_tag"}


@dataclass(frozen=True)
class AdSentimentOutputs:
    joined_parquet: Path
    summary_json: Path
    summary_csv: Path


def _normalize_sentiment(value: str) -> str:
    label = str(value or "").strip().lower()
    if label in {"pos", "positive"}:
        return "positive"
    if label in {"neu", "neutral"}:
        return "neutral"
    if label in {"neg", "negative"}:
        return "negative"
    return ""


def _load_sentiment_records(path: Path) -> pd.DataFrame:
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("records", [])
    frame = pd.DataFrame(records)
    missing = REQUIRED_SENTIMENT_COLUMNS.difference(frame.columns)
    if missing:
        missing_cols = ", ".join(sorted(missing))
        raise ValueError(f"Sentiment file missing required columns: {missing_cols}")

    frame = frame.copy()
    frame["tweet_id"] = frame["tweet_id"].astype(str).str.strip()
    if "pipeline_row_id" in frame.columns:
        frame["pipeline_row_id"] = frame["pipeline_row_id"].astype(str).str.strip()
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    frame["sentiment"] = frame["sentiment"].map(_normalize_sentiment)
    frame["confidence"] = pd.to_numeric(frame["confidence"], errors="coerce")
    frame = frame.dropna(subset=["year", "confidence"])
    frame = frame[frame["sentiment"].isin(["positive", "neutral", "negative"])]
    frame["year"] = frame["year"].astype(int)
    return frame


def _load_enriched_rows(path: Path, year: int) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = REQUIRED_ENRICHED_COLUMNS.difference(frame.columns)
    if missing:
        missing_cols = ", ".join(sorted(missing))
        raise ValueError(f"Enriched file missing required columns: {missing_cols}")

    def _series_or_default(column: str, default: str) -> pd.Series:
        if column in frame.columns:
            return frame[column]
        return pd.Series([default] * len(frame), index=frame.index)

    selected = pd.DataFrame(
        {
            "tweet_id": frame["id"].astype(str).str.strip(),
            "year": int(year),
            "ad_tag": _series_or_default("ad_tag", "unknown_ad").astype(str).str.strip(),
            "brand_tag": _series_or_default("brand_tag", "unknown_brand").astype(str).str.strip(),
            "game_phase": _series_or_default("game_phase", "unknown").astype(str).str.strip(),
            "pipeline_row_id": _series_or_default("pipeline_row_id", "").astype(str).str.strip(),
        }
    )
    selected["ad_tag"] = selected["ad_tag"].replace("", "unknown_ad")
    selected["brand_tag"] = selected["brand_tag"].replace("", "unknown_brand")
    selected["game_phase"] = selected["game_phase"].replace("", "unknown")
    return selected


def _load_brand_tweet_map(path: Path) -> dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    mapping: dict[str, str] = {}
    for record in payload.get("records", []):
        key = str(record.get("pipeline_row_id") or record.get("tweet_id") or "").strip()
        brand = str(record.get("primary_brand", "")).strip()
        if key and brand:
            mapping[key] = brand
    return mapping


def _build_summary(joined: pd.DataFrame, *, min_tweets: int) -> list[dict[str, Any]]:
    if joined.empty:
        return []

    working = joined.copy()
    working["score"] = working["sentiment"].map({"negative": -1.0, "neutral": 0.0, "positive": 1.0})
    working["weighted_score"] = working["score"] * working["confidence"]

    rows: list[dict[str, Any]] = []
    grouped = working.groupby("ad_tag", sort=True)
    for ad_tag, group in grouped:
        total = int(len(group))
        if total < min_tweets:
            continue

        sentiment_counts = group["sentiment"].value_counts()
        positive = int(sentiment_counts.get("positive", 0))
        neutral = int(sentiment_counts.get("neutral", 0))
        negative = int(sentiment_counts.get("negative", 0))

        confidence_sum = float(group["confidence"].sum())
        weighted_net = 0.0
        if confidence_sum > 0:
            weighted_net = float(group["weighted_score"].sum() / confidence_sum)

        rows.append(
            {
                "ad_tag": str(ad_tag),
                "tweet_count": total,
                "positive_count": positive,
                "neutral_count": neutral,
                "negative_count": negative,
                "positive_rate": round(positive / total, 6),
                "neutral_rate": round(neutral / total, 6),
                "negative_rate": round(negative / total, 6),
                "net_sentiment": round((positive - negative) / total, 6),
                "avg_confidence": round(float(group["confidence"].mean()), 6),
                "weighted_net_sentiment": round(weighted_net, 6),
            }
        )

    rows.sort(key=lambda row: (-int(row["tweet_count"]), str(row["ad_tag"])))
    return rows


def run_ad_sentiment_analysis(
    *,
    year: int,
    sentiment_path: Path,
    enriched_path: Path,
    output_dir: Path,
    min_tweets: int = 1,
    tweet_map_path: Path | None = None,
    logger=None,
):
    if min_tweets < 1:
        raise ValueError("min_tweets must be >= 1")
    if not sentiment_path.exists():
        raise ValueError(f"Missing sentiment input file: {sentiment_path}")
    if not enriched_path.exists():
        raise ValueError(f"Missing enriched input file: {enriched_path}")

    if tweet_map_path and not tweet_map_path.exists():
        raise ValueError(f"Missing tweet map file: {tweet_map_path}")

    if logger:
        logger(f"[ad-sentiment] loading sentiment from {sentiment_path}")
    sentiment = _load_sentiment_records(sentiment_path)
    if logger:
        logger(f"[ad-sentiment] loading enriched rows from {enriched_path}")
    enriched = _load_enriched_rows(enriched_path, year)

    if logger:
        logger("[ad-sentiment] joining sentiment with enriched rows")
    join_keys = ["tweet_id", "year"]
    if "pipeline_row_id" in sentiment.columns and "pipeline_row_id" in enriched.columns:
        join_keys = ["pipeline_row_id", "year"]
    joined = sentiment.merge(enriched, on=join_keys, how="left", indicator=True)
    joined["join_status"] = joined.pop("_merge")
    joined["ad_tag"] = joined["ad_tag"].fillna("unmatched")
    joined["brand_tag"] = joined["brand_tag"].fillna("unmatched")
    joined["game_phase"] = joined["game_phase"].fillna("unknown")

    if "tweet_id" not in joined.columns:
        joined["tweet_id"] = joined.get("tweet_id_x", "").astype(str)
    if "year" not in joined.columns:
        joined["year"] = joined.get("year_x", joined.get("year_y", "")).astype(str)

    if tweet_map_path:
        if logger:
            logger(f"[ad-sentiment] loading tweet map from {tweet_map_path}")
        tweet_map = _load_brand_tweet_map(tweet_map_path)
        key_series = joined["pipeline_row_id"] if "pipeline_row_id" in joined.columns else joined["tweet_id"]
        mapped_brand = key_series.map(lambda key: tweet_map.get(str(key).strip(), ""))
        unknown_mask = joined["ad_tag"].isin(["", "unknown_ad", "unmatched"])
        joined.loc[unknown_mask & mapped_brand.ne(""), "ad_tag"] = mapped_brand[unknown_mask & mapped_brand.ne("")]

    joined = joined.sort_values(by=["tweet_id", "year"], kind="mergesort")
    summary_rows = _build_summary(joined, min_tweets=min_tweets)

    output_dir.mkdir(parents=True, exist_ok=True)
    joined_out = output_dir / "ad_sentiment_joined.parquet"
    summary_json = output_dir / "ad_sentiment_summary.json"
    summary_csv = output_dir / "ad_sentiment_summary.csv"

    joined.to_parquet(joined_out, index=False)
    summary_json.write_text(
        json.dumps(
            {
                "year": year,
                "total_sentiment_rows": int(len(sentiment)),
                "joined_rows": int(len(joined)),
                "matched_rows": int((joined["join_status"] == "both").sum()),
                "unmatched_rows": int((joined["join_status"] != "both").sum()),
                "min_tweets": int(min_tweets),
                "ads": summary_rows,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    pd.DataFrame(summary_rows).to_csv(summary_csv, index=False)
    if logger:
        logger(f"[ad-sentiment] wrote outputs to {output_dir}")

    notes = [
        f"matched_rows={(joined['join_status'] == 'both').sum()}",
        f"unmatched_rows={(joined['join_status'] != 'both').sum()}",
        f"min_tweets={min_tweets}",
    ]
    manifest = make_manifest(
        [sentiment_path, enriched_path],
        [joined_out, summary_json, summary_csv],
        len(sentiment),
        len(joined),
        notes=notes,
    )
    if logger:
        logger("[ad-sentiment] complete")

    return AdSentimentOutputs(joined_parquet=joined_out, summary_json=summary_json, summary_csv=summary_csv), manifest
