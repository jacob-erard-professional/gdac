import json
from pathlib import Path
from typing import Any

import pandas as pd


def _load_brand_groups(path: Path) -> tuple[dict[str, str], dict[str, int]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    brands = payload.get("brands", [])
    hashtag_to_brand: dict[str, str] = {}
    hashtag_to_count: dict[str, int] = {}
    for brand in brands:
        label = str(brand.get("brand", "")).strip().lower()
        for item in brand.get("hashtags", []):
            tag = str(item.get("hashtag", "")).strip().lower()
            if not tag:
                continue
            hashtag_to_brand[tag] = label or tag
            try:
                hashtag_to_count[tag] = int(item.get("count", 0))
            except (TypeError, ValueError):
                hashtag_to_count[tag] = 0
    return hashtag_to_brand, hashtag_to_count


def _load_parent_company_groups(path: Path) -> dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    mapping: dict[str, str] = {}
    for group in payload.get("parent_companies", []):
        parent = str(group.get("parent_company", "")).strip().lower()
        if not parent:
            continue
        for item in group.get("brands", []):
            brand = str(item.get("brand", "")).strip().lower()
            if brand:
                mapping[brand] = parent
    return mapping


def _parse_hashtags(raw: str) -> list[str]:
    if raw is None:
        return []
    tags = []
    for tag in str(raw).split("|"):
        cleaned = tag.strip().lower()
        if cleaned:
            tags.append(cleaned)
    return tags


def _brand_scores(tags: list[str], hashtag_to_brand: dict[str, str], hashtag_to_count: dict[str, int]) -> dict[str, int]:
    scores: dict[str, int] = {}
    for tag in tags:
        brand = hashtag_to_brand.get(tag)
        if not brand:
            continue
        scores[brand] = scores.get(brand, 0) + max(hashtag_to_count.get(tag, 1), 1)
    return scores


def _select_primary(scores: dict[str, int]) -> str:
    if not scores:
        return "unmatched"
    ordered = sorted(scores.items(), key=lambda item: (-int(item[1]), str(item[0])))
    return str(ordered[0][0])


def build_brand_tweet_map(
    *,
    enriched_path: Path,
    brand_groups_path: Path,
    output_path: Path,
    year: int | None = None,
) -> Path:
    if not enriched_path.exists():
        raise ValueError(f"Missing enriched file: {enriched_path}")
    if not brand_groups_path.exists():
        raise ValueError(f"Missing brand groups file: {brand_groups_path}")

    hashtag_to_brand, hashtag_to_count = _load_brand_groups(brand_groups_path)
    frame = pd.read_csv(enriched_path, dtype=str, keep_default_na=False)

    tweet_id_col = "id" if "id" in frame.columns else ("tweet_id" if "tweet_id" in frame.columns else None)
    if tweet_id_col is None:
        raise ValueError("Enriched file missing tweet id column: id or tweet_id")
    pipeline_col = "pipeline_row_id" if "pipeline_row_id" in frame.columns else None

    records: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        tags = _parse_hashtags(row.get("hashtags", ""))
        scores = _brand_scores(tags, hashtag_to_brand, hashtag_to_count)
        ordered_brands = sorted(scores.items(), key=lambda item: (-int(item[1]), str(item[0])))
        brand_tags = [str(item[0]) for item in ordered_brands]
        record = {
            "tweet_id": str(row.get(tweet_id_col, "")).strip(),
            "brand_tags": brand_tags,
            "primary_brand": _select_primary(scores),
        }
        if pipeline_col:
            record["pipeline_row_id"] = str(row.get(pipeline_col, "")).strip()
        if "year" in frame.columns:
            record["year"] = int(row.get("year")) if str(row.get("year", "")).strip().isdigit() else None
        elif year is not None:
            record["year"] = int(year)
        records.append(record)

    payload = {
        "year": year,
        "source_enriched": str(enriched_path),
        "source_brand_groups": str(brand_groups_path),
        "records": records,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def build_parent_company_tweet_map(
    *,
    brand_tweet_map_path: Path,
    parent_company_groups_path: Path,
    output_path: Path,
    year: int | None = None,
) -> Path:
    if not brand_tweet_map_path.exists():
        raise ValueError(f"Missing brand tweet map file: {brand_tweet_map_path}")
    if not parent_company_groups_path.exists():
        raise ValueError(f"Missing parent company groups file: {parent_company_groups_path}")

    parent_map = _load_parent_company_groups(parent_company_groups_path)
    payload = json.loads(brand_tweet_map_path.read_text(encoding="utf-8"))
    records = payload.get("records", [])

    out_records: list[dict[str, Any]] = []
    for record in records:
        brand_tags = [str(tag).strip().lower() for tag in record.get("brand_tags", []) if str(tag).strip()]
        primary_brand = str(record.get("primary_brand", "")).strip().lower()
        parent_tags = []
        for brand in brand_tags:
            parent = parent_map.get(brand)
            if parent:
                parent_tags.append(parent)
        primary_parent = parent_map.get(primary_brand, "")
        if not primary_parent and parent_tags:
            primary_parent = sorted(parent_tags)[0]

        out_record = {
            "tweet_id": str(record.get("tweet_id", "")).strip(),
            "brand_tags": brand_tags,
            "primary_brand": primary_brand or "unmatched",
            "parent_company_tags": sorted(set(parent_tags)),
            "primary_parent_company": primary_parent or "unmatched",
        }
        if "pipeline_row_id" in record:
            out_record["pipeline_row_id"] = str(record.get("pipeline_row_id", "")).strip()
        if record.get("year") is not None:
            out_record["year"] = record.get("year")
        elif year is not None:
            out_record["year"] = int(year)
        out_records.append(out_record)

    out_payload = {
        "year": year,
        "source_brand_tweet_map": str(brand_tweet_map_path),
        "source_parent_company_groups": str(parent_company_groups_path),
        "records": out_records,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(out_payload, indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def build_parent_company_tweet_map_jsonl(
    *,
    enriched_path: Path,
    brand_groups_path: Path,
    parent_company_groups_path: Path,
    output_path: Path,
    year: int | None = None,
    batch_size: int = 1000,
) -> Path:
    if batch_size < 1:
        raise ValueError("batch_size must be >= 1")
    if not enriched_path.exists():
        raise ValueError(f"Missing enriched file: {enriched_path}")
    if not brand_groups_path.exists():
        raise ValueError(f"Missing brand groups file: {brand_groups_path}")
    if not parent_company_groups_path.exists():
        raise ValueError(f"Missing parent company groups file: {parent_company_groups_path}")

    hashtag_to_brand, hashtag_to_count = _load_brand_groups(brand_groups_path)
    parent_map = _load_parent_company_groups(parent_company_groups_path)
    frame = pd.read_csv(enriched_path, dtype=str, keep_default_na=False)

    tweet_id_col = "id" if "id" in frame.columns else ("tweet_id" if "tweet_id" in frame.columns else None)
    if tweet_id_col is None:
        raise ValueError("Enriched file missing tweet id column: id or tweet_id")
    pipeline_col = "pipeline_row_id" if "pipeline_row_id" in frame.columns else None

    output_path.parent.mkdir(parents=True, exist_ok=True)
    total = len(frame)
    with output_path.open("w", encoding="utf-8") as f:
        for start in range(0, total, batch_size):
            batch = frame.iloc[start : start + batch_size]
            records: list[dict[str, Any]] = []
            for _, row in batch.iterrows():
                tags = _parse_hashtags(row.get("hashtags", ""))
                scores = _brand_scores(tags, hashtag_to_brand, hashtag_to_count)
                primary_brand = _select_primary(scores)
                parent = parent_map.get(primary_brand, "unmatched")
                record = {
                    "tweet_id": str(row.get(tweet_id_col, "")).strip(),
                    "primary_brand": primary_brand,
                    "parent_company": parent,
                }
                if pipeline_col:
                    record["pipeline_row_id"] = str(row.get(pipeline_col, "")).strip()
                if "year" in frame.columns:
                    record["year"] = int(row.get("year")) if str(row.get("year", "")).strip().isdigit() else None
                elif year is not None:
                    record["year"] = int(year)
                records.append(record)

            payload = {
                "batch_start": int(start),
                "batch_size": int(len(batch)),
                "records": records,
            }
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
            print(
                f"[tweet-map] wrote batch {start // batch_size + 1} "
                f"rows={len(batch)} total={total}"
            )
    return output_path
