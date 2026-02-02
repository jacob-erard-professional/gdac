def run(rows: list[dict], min_text_length: int = 3) -> tuple[list[dict], dict]:
    cleaned: list[dict] = []
    rejected = 0
    breakdown: dict[str, int] = {}
    for row in rows:
        txt = str(row.get("text", "")).strip()
        if len(txt) < min_text_length:
            rejected += 1
            key = "short_or_empty_text"
            breakdown[key] = breakdown.get(key, 0) + 1
            continue
        cleaned.append(
            {
                "source_record_id": row["source_record_id"],
                "event_name": row["event_name"],
                "year": row["year"],
                "normalized_text": txt.lower(),
                "is_valid": True,
                "brand_ad_name": row.get("brand_ad_name", ""),
                "retweet_count": row.get("retweet_count", "0"),
                "like_count": row.get("like_count", "0"),
                "reply_count": row.get("reply_count", "0"),
                "quote_count": row.get("quote_count", "0"),
                "raw_hashtags": row.get("raw_hashtags", ""),
                "raw_mentions": row.get("raw_mentions", ""),
            }
        )
    return cleaned, {"accepted": len(cleaned), "rejected": rejected, "rejection_breakdown": breakdown}
