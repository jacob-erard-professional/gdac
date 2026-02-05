import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.pipeline.stage_runtime import make_manifest

REQUIRED_SENTIMENT_COLUMNS = {"tweet_id", "year", "sentiment", "confidence", "text"}
REQUIRED_ENRICHED_COLUMNS = {"id"}
TIME_SLICE_MINUTES = 15


@dataclass(frozen=True)
class ParentCompanySentimentOutputs:
    joined_parquet: Path
    summary_json: Path
    summary_csv: Path
    timeslices_json: Path
    timeslices_csv: Path
    ad_tag_json: Path
    ad_tag_csv: Path


def _normalize_label(value: str) -> str:
    return str(value or "").strip().lower()


def _normalize_sentiment(value: str) -> str:
    label = _normalize_label(value)
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

    created_at_col = "created_at_utc" if "created_at_utc" in frame.columns else "created_at"

    selected = pd.DataFrame(
        {
            "tweet_id": frame["id"].astype(str).str.strip(),
            "year": int(year),
            "brand_tag": frame.get("brand_tag", "unknown_brand").astype(str).str.strip(),
            "ad_tag": frame.get("ad_tag", "unknown_ad").astype(str).str.strip(),
            "game_phase": frame.get("game_phase", "unknown").astype(str).str.strip(),
            "created_at": frame.get(created_at_col, "").astype(str).str.strip(),
        }
    )
    selected["brand_tag"] = selected["brand_tag"].replace("", "unknown_brand")
    selected["ad_tag"] = selected["ad_tag"].replace("", "unknown_ad")
    selected["game_phase"] = selected["game_phase"].replace("", "unknown")
    selected["created_at"] = selected["created_at"].replace("", pd.NA)
    return selected


def _load_parent_company_groups(path: Path) -> dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    groups = payload.get("parent_companies", [])
    mapping: dict[str, str] = {}
    for group in groups:
        parent = _normalize_label(group.get("parent_company", ""))
        if not parent:
            continue
        for brand in group.get("brands", []):
            brand_label = _normalize_label(brand.get("brand", ""))
            if brand_label:
                mapping[brand_label] = parent
    return mapping


def _assign_parent_company(row: pd.Series, mapping: dict[str, str]) -> str:
    brand = _normalize_label(row.get("brand_tag", ""))
    ad = _normalize_label(row.get("ad_tag", ""))
    return mapping.get(brand) or mapping.get(ad) or "unmatched"


def _weighted_net_sentiment(frame: pd.DataFrame) -> float:
    confidence_sum = float(frame["confidence"].sum())
    if confidence_sum <= 0:
        return 0.0
    return float(frame["weighted_score"].sum() / confidence_sum)


def _build_summary(joined: pd.DataFrame, *, min_tweets: int, overall_weighted_net: float) -> list[dict[str, Any]]:
    if joined.empty:
        return []

    working = joined.copy()
    working["score"] = working["sentiment"].map({"negative": -1.0, "neutral": 0.0, "positive": 1.0})
    working["weighted_score"] = working["score"] * working["confidence"]

    rows: list[dict[str, Any]] = []
    grouped = working.groupby("parent_company", sort=True)
    for parent, group in grouped:
        total = int(len(group))
        if total < min_tweets:
            continue

        sentiment_counts = group["sentiment"].value_counts()
        positive = int(sentiment_counts.get("positive", 0))
        neutral = int(sentiment_counts.get("neutral", 0))
        negative = int(sentiment_counts.get("negative", 0))

        weighted_net = _weighted_net_sentiment(group)
        weighted_lift = weighted_net - overall_weighted_net

        rows.append(
            {
                "parent_company": str(parent),
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
                "weighted_lift_vs_overall": round(weighted_lift, 6),
            }
        )

    rows.sort(key=lambda row: (-int(row["tweet_count"]), str(row["parent_company"])))
    return rows


def _build_time_slices(joined: pd.DataFrame, *, min_tweets: int, overall_weighted_net: float) -> list[dict[str, Any]]:
    if joined.empty:
        return []

    working = joined.copy()
    working["timestamp"] = pd.to_datetime(working["created_at"], errors="coerce", utc=True)
    working = working.dropna(subset=["timestamp"])
    if working.empty:
        return []

    working["time_slice"] = working["timestamp"].dt.floor(f"{TIME_SLICE_MINUTES}min")
    rows: list[dict[str, Any]] = []
    grouped = working.groupby(["parent_company", "time_slice"], sort=True)
    for (parent, time_slice), group in grouped:
        total = int(len(group))
        if total < min_tweets:
            continue
        sentiment_counts = group["sentiment"].value_counts()
        positive = int(sentiment_counts.get("positive", 0))
        neutral = int(sentiment_counts.get("neutral", 0))
        negative = int(sentiment_counts.get("negative", 0))

        weighted_net = _weighted_net_sentiment(group)
        weighted_lift = weighted_net - overall_weighted_net

        rows.append(
            {
                "parent_company": str(parent),
                "time_slice_start": time_slice.isoformat(),
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
                "weighted_lift_vs_overall": round(weighted_lift, 6),
            }
        )

    rows.sort(key=lambda row: (row["time_slice_start"], str(row["parent_company"])))
    return rows


def _build_ad_tag_summary(joined: pd.DataFrame, *, min_tweets: int, overall_weighted_net: float) -> list[dict[str, Any]]:
    if joined.empty:
        return []

    working = joined.copy()
    working["ad_tag_norm"] = working["ad_tag"].map(_normalize_label).replace("", "unknown_ad")
    rows: list[dict[str, Any]] = []
    grouped = working.groupby(["parent_company", "ad_tag_norm"], sort=True)
    for (parent, ad_tag), group in grouped:
        total = int(len(group))
        if total < min_tweets:
            continue
        sentiment_counts = group["sentiment"].value_counts()
        positive = int(sentiment_counts.get("positive", 0))
        neutral = int(sentiment_counts.get("neutral", 0))
        negative = int(sentiment_counts.get("negative", 0))

        weighted_net = _weighted_net_sentiment(group)
        weighted_lift = weighted_net - overall_weighted_net

        rows.append(
            {
                "parent_company": str(parent),
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
                "weighted_lift_vs_overall": round(weighted_lift, 6),
            }
        )

    rows.sort(key=lambda row: (-int(row["tweet_count"]), str(row["parent_company"]), str(row["ad_tag"])))
    return rows


def run_parent_company_sentiment_analysis(
    *,
    year: int,
    sentiment_path: Path,
    enriched_path: Path,
    parent_groups_path: Path,
    output_dir: Path,
    min_tweets: int = 1,
):
    if min_tweets < 1:
        raise ValueError("min_tweets must be >= 1")
    if not sentiment_path.exists():
        raise ValueError(f"Missing sentiment input file: {sentiment_path}")
    if not enriched_path.exists():
        raise ValueError(f"Missing enriched input file: {enriched_path}")
    if not parent_groups_path.exists():
        raise ValueError(f"Missing parent company groups file: {parent_groups_path}")

    sentiment = _load_sentiment_records(sentiment_path)
    enriched = _load_enriched_rows(enriched_path, year)
    parent_mapping = _load_parent_company_groups(parent_groups_path)

    joined = sentiment.merge(enriched, on=["tweet_id", "year"], how="left", indicator=True)
    joined["join_status"] = joined.pop("_merge")
    joined["parent_company"] = joined.apply(lambda row: _assign_parent_company(row, parent_mapping), axis=1)

    joined = joined.sort_values(by=["tweet_id", "year"], kind="mergesort")
    joined["score"] = joined["sentiment"].map({"negative": -1.0, "neutral": 0.0, "positive": 1.0})
    joined["weighted_score"] = joined["score"] * joined["confidence"]
    overall_weighted_net = _weighted_net_sentiment(joined)
    summary_rows = _build_summary(joined, min_tweets=min_tweets, overall_weighted_net=overall_weighted_net)
    timeslice_rows = _build_time_slices(joined, min_tweets=min_tweets, overall_weighted_net=overall_weighted_net)
    ad_tag_rows = _build_ad_tag_summary(joined, min_tweets=min_tweets, overall_weighted_net=overall_weighted_net)

    output_dir.mkdir(parents=True, exist_ok=True)
    joined_out = output_dir / "parent_company_sentiment_joined.parquet"
    summary_json = output_dir / "parent_company_sentiment_summary.json"
    summary_csv = output_dir / "parent_company_sentiment_summary.csv"
    timeslices_json = output_dir / "parent_company_sentiment_timeslices.json"
    timeslices_csv = output_dir / "parent_company_sentiment_timeslices.csv"
    ad_tag_json = output_dir / "parent_company_sentiment_by_ad_tag.json"
    ad_tag_csv = output_dir / "parent_company_sentiment_by_ad_tag.csv"

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
                "overall_weighted_net_sentiment": round(overall_weighted_net, 6),
                "parents": summary_rows,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    pd.DataFrame(summary_rows).to_csv(summary_csv, index=False)
    timeslices_json.write_text(
        json.dumps(
            {
                "year": year,
                "min_tweets": int(min_tweets),
                "overall_weighted_net_sentiment": round(overall_weighted_net, 6),
                "time_slice_minutes": TIME_SLICE_MINUTES,
                "time_slices": timeslice_rows,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    pd.DataFrame(timeslice_rows).to_csv(timeslices_csv, index=False)
    ad_tag_json.write_text(
        json.dumps(
            {
                "year": year,
                "min_tweets": int(min_tweets),
                "overall_weighted_net_sentiment": round(overall_weighted_net, 6),
                "groups": ad_tag_rows,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    pd.DataFrame(ad_tag_rows).to_csv(ad_tag_csv, index=False)

    notes = [
        f"matched_rows={(joined['join_status'] == 'both').sum()}",
        f"unmatched_rows={(joined['join_status'] != 'both').sum()}",
        f"min_tweets={min_tweets}",
    ]
    manifest = make_manifest(
        [sentiment_path, enriched_path, parent_groups_path],
        [joined_out, summary_json, summary_csv, timeslices_json, timeslices_csv, ad_tag_json, ad_tag_csv],
        len(sentiment),
        len(joined),
        notes=notes,
    )

    return (
        ParentCompanySentimentOutputs(
            joined_parquet=joined_out,
            summary_json=summary_json,
            summary_csv=summary_csv,
            timeslices_json=timeslices_json,
            timeslices_csv=timeslices_csv,
            ad_tag_json=ad_tag_json,
            ad_tag_csv=ad_tag_csv,
        ),
        manifest,
    )
