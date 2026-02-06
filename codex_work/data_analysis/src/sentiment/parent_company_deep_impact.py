import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.pipeline.stage_runtime import make_manifest
from src.sentiment.deep_emotion import REQUIRED_EMOTIONS

REQUIRED_DEEP_COLUMNS = {"tweet_id", "year", "main_sentiment", "confidence"}
REQUIRED_ENRICHED_COLUMNS = {"id"}
TIME_SLICE_MINUTES = 15


@dataclass(frozen=True)
class ParentCompanyDeepSentimentOutputs:
    joined_parquet: Path
    summary_json: Path
    summary_csv: Path
    timeslices_json: Path
    timeslices_csv: Path


def _normalize_label(value: str) -> str:
    return str(value or "").strip().lower()


def _load_deep_records(path: Path) -> pd.DataFrame:
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("records", [])
    frame = pd.DataFrame(records)
    missing = REQUIRED_DEEP_COLUMNS.difference(frame.columns)
    if missing:
        missing_cols = ", ".join(sorted(missing))
        raise ValueError(f"Deep sentiment file missing required columns: {missing_cols}")

    frame = frame.copy()
    frame["tweet_id"] = frame["tweet_id"].astype(str).str.strip()
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    frame["main_sentiment"] = frame["main_sentiment"].map(_normalize_label)
    frame["confidence"] = pd.to_numeric(frame["confidence"], errors="coerce")
    if "pipeline_row_id" in frame.columns:
        frame["pipeline_row_id"] = frame["pipeline_row_id"].astype(str).str.strip()
    frame = frame.dropna(subset=["year", "confidence"])
    frame = frame[frame["main_sentiment"].isin(REQUIRED_EMOTIONS)]
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
            "pipeline_row_id": frame.get("pipeline_row_id", "").astype(str).str.strip(),
            "created_at": frame.get(created_at_col, "").astype(str).str.strip(),
        }
    )
    selected["brand_tag"] = selected["brand_tag"].replace("", "unknown_brand")
    selected["ad_tag"] = selected["ad_tag"].replace("", "unknown_ad")
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


def _load_parent_company_tweet_map(path: Path) -> pd.DataFrame:
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("records", [])
    frame = pd.DataFrame(records)
    if frame.empty:
        return frame
    if "pipeline_row_id" in frame.columns:
        frame["pipeline_row_id"] = frame["pipeline_row_id"].astype(str).str.strip()
    if "tweet_id" in frame.columns:
        frame["tweet_id"] = frame["tweet_id"].astype(str).str.strip()
    if "primary_parent_company" in frame.columns:
        frame["primary_parent_company"] = frame["primary_parent_company"].astype(str).str.strip()
    return frame


def _assign_parent_company(row: pd.Series, mapping: dict[str, str]) -> str:
    brand = _normalize_label(row.get("brand_tag", ""))
    ad = _normalize_label(row.get("ad_tag", ""))
    return mapping.get(brand) or mapping.get(ad) or "unmatched"


def _build_summary(joined: pd.DataFrame, *, min_tweets: int) -> list[dict[str, Any]]:
    if joined.empty:
        return []

    rows: list[dict[str, Any]] = []
    grouped = joined.groupby("parent_company", sort=True)
    emotions = sorted(REQUIRED_EMOTIONS)
    for parent, group in grouped:
        total = int(len(group))
        if total < min_tweets:
            continue

        counts = group["main_sentiment"].value_counts()
        row: dict[str, Any] = {
            "parent_company": str(parent),
            "tweet_count": total,
            "avg_confidence": round(float(group["confidence"].mean()), 6),
        }
        for emotion in emotions:
            count = int(counts.get(emotion, 0))
            row[f"{emotion}_count"] = count
            row[f"{emotion}_rate"] = round(count / total, 6)

        rows.append(row)

    rows.sort(key=lambda row: (-int(row["tweet_count"]), str(row["parent_company"])))
    return rows


def _build_time_slices(joined: pd.DataFrame, *, min_tweets: int) -> list[dict[str, Any]]:
    if joined.empty:
        return []

    working = joined.copy()
    if "created_at" not in working.columns:
        return []
    working["timestamp"] = pd.to_datetime(working["created_at"], errors="coerce", utc=True)
    working = working.dropna(subset=["timestamp"])
    if working.empty:
        return []

    working["time_slice"] = working["timestamp"].dt.floor(f"{TIME_SLICE_MINUTES}min")
    rows: list[dict[str, Any]] = []
    grouped = working.groupby(["parent_company", "time_slice"], sort=True)
    emotions = sorted(REQUIRED_EMOTIONS)
    for (parent, time_slice), group in grouped:
        total = int(len(group))
        if total < min_tweets:
            continue

        counts = group["main_sentiment"].value_counts()
        row: dict[str, Any] = {
            "parent_company": str(parent),
            "time_slice_start": time_slice.isoformat(),
            "tweet_count": total,
            "avg_confidence": round(float(group["confidence"].mean()), 6),
        }
        for emotion in emotions:
            count = int(counts.get(emotion, 0))
            row[f"{emotion}_count"] = count
            row[f"{emotion}_rate"] = round(count / total, 6)

        rows.append(row)

    rows.sort(key=lambda row: (row["time_slice_start"], str(row["parent_company"])))
    return rows


def run_parent_company_deep_sentiment_analysis(
    *,
    year: int,
    deep_sentiment_path: Path,
    enriched_path: Path,
    parent_groups_path: Path,
    output_dir: Path,
    min_tweets: int = 1,
    tweet_map_path: Path | None = None,
):
    if min_tweets < 1:
        raise ValueError("min_tweets must be >= 1")
    if not deep_sentiment_path.exists():
        raise ValueError(f"Missing deep sentiment input file: {deep_sentiment_path}")
    if not enriched_path.exists():
        raise ValueError(f"Missing enriched input file: {enriched_path}")
    if not parent_groups_path.exists():
        raise ValueError(f"Missing parent company groups file: {parent_groups_path}")
    if tweet_map_path and not tweet_map_path.exists():
        tweet_map_path = None

    deep_sentiment = _load_deep_records(deep_sentiment_path)
    enriched = _load_enriched_rows(enriched_path, year)
    parent_mapping = _load_parent_company_groups(parent_groups_path)

    join_keys = ["tweet_id", "year"]
    if "pipeline_row_id" in deep_sentiment.columns and "pipeline_row_id" in enriched.columns:
        join_keys = ["pipeline_row_id", "year"]
    joined = deep_sentiment.merge(enriched, on=join_keys, how="left", indicator=True)
    joined["join_status"] = joined.pop("_merge")
    joined["parent_company"] = joined.apply(lambda row: _assign_parent_company(row, parent_mapping), axis=1)

    if tweet_map_path:
        tweet_map = _load_parent_company_tweet_map(tweet_map_path)
        if not tweet_map.empty:
            map_join_keys = ["tweet_id"]
            if "pipeline_row_id" in joined.columns and "pipeline_row_id" in tweet_map.columns:
                map_join_keys = ["pipeline_row_id"]
            joined = joined.merge(
                tweet_map[map_join_keys + ["primary_parent_company"]],
                on=map_join_keys,
                how="left",
            )
            joined["parent_company"] = joined["primary_parent_company"].fillna(joined["parent_company"])
            joined = joined.drop(columns=["primary_parent_company"])

    if "tweet_id" not in joined.columns:
        joined["tweet_id"] = joined.get("tweet_id_x", "").astype(str)
    if "year" not in joined.columns:
        joined["year"] = joined.get("year_x", joined.get("year_y", "")).astype(str)
    joined = joined.sort_values(by=["tweet_id", "year"], kind="mergesort")
    summary_rows = _build_summary(joined, min_tweets=min_tweets)
    timeslice_rows = _build_time_slices(joined, min_tweets=min_tweets)

    output_dir.mkdir(parents=True, exist_ok=True)
    joined_out = output_dir / "parent_company_deep_sentiment_joined.parquet"
    summary_json = output_dir / "parent_company_deep_sentiment_summary.json"
    summary_csv = output_dir / "parent_company_deep_sentiment_summary.csv"
    timeslices_json = output_dir / "parent_company_deep_sentiment_timeslices.json"
    timeslices_csv = output_dir / "parent_company_deep_sentiment_timeslices.csv"

    joined.to_parquet(joined_out, index=False)
    summary_json.write_text(
        json.dumps(
            {
                "year": year,
                "total_records": int(len(deep_sentiment)),
                "joined_rows": int(len(joined)),
                "matched_rows": int((joined["join_status"] == "both").sum()),
                "unmatched_rows": int((joined["join_status"] != "both").sum()),
                "min_tweets": int(min_tweets),
                "emotions": sorted(REQUIRED_EMOTIONS),
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
                "time_slice_minutes": TIME_SLICE_MINUTES,
                "emotions": sorted(REQUIRED_EMOTIONS),
                "time_slices": timeslice_rows,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    pd.DataFrame(timeslice_rows).to_csv(timeslices_csv, index=False)

    notes = [
        f"matched_rows={(joined['join_status'] == 'both').sum()}",
        f"unmatched_rows={(joined['join_status'] != 'both').sum()}",
        f"min_tweets={min_tweets}",
    ]
    manifest = make_manifest(
        [deep_sentiment_path, enriched_path, parent_groups_path],
        [joined_out, summary_json, summary_csv, timeslices_json, timeslices_csv],
        len(deep_sentiment),
        len(joined),
        notes=notes,
    )

    return ParentCompanyDeepSentimentOutputs(
        joined_parquet=joined_out,
        summary_json=summary_json,
        summary_csv=summary_csv,
        timeslices_json=timeslices_json,
        timeslices_csv=timeslices_csv,
    ), manifest
