from collections import Counter
import ast
import re


def run(rows: list[dict], run_id: str, event_name: str, year: int, keywords: list[str]) -> list[dict]:
    total = len(rows)
    valid = sum(1 for r in rows if r.get("is_valid", True))
    lowered_keywords = [k.lower() for k in keywords]
    keyword_hits = 0
    for row in rows:
        text = str(row.get("normalized_text", "")).lower()
        keyword_hits += sum(1 for kw in lowered_keywords if kw in text)

    counter = Counter({"total_posts": total, "valid_posts": valid})
    rate = (keyword_hits / total) if total else 0.0
    return [
        {"run_id": run_id, "event_name": event_name, "year": year, "kpi_id": "total_posts", "value": float(counter["total_posts"])},
        {"run_id": run_id, "event_name": event_name, "year": year, "kpi_id": "valid_posts", "value": float(counter["valid_posts"])},
        {"run_id": run_id, "event_name": event_name, "year": year, "kpi_id": "keyword_hit_rate", "value": float(rate)},
    ]


def init_accumulator(keywords: list[str]) -> dict:
    return {
        "total_posts": 0,
        "valid_posts": 0,
        "keyword_hits": 0,
        "keywords": [k.lower() for k in keywords],
        "hashtag_counts": Counter(),
        "mention_counts": Counter(),
    }


def update_accumulator(acc: dict, rows: list[dict]) -> None:
    acc["total_posts"] += len(rows)
    acc["valid_posts"] += sum(1 for r in rows if r.get("is_valid", True))
    for row in rows:
        text = str(row.get("normalized_text", "")).lower()
        acc["keyword_hits"] += sum(1 for kw in acc["keywords"] if kw in text)
        for tag in _extract_hashtags(row):
            acc["hashtag_counts"][tag.lower()] += 1
        for mention in _extract_mentions(row):
            acc["mention_counts"][mention.lower()] += 1


def finalize_accumulator(acc: dict, run_id: str, event_name: str, year: int) -> list[dict]:
    total = int(acc["total_posts"])
    valid = int(acc["valid_posts"])
    rate = (float(acc["keyword_hits"]) / total) if total else 0.0
    return [
        {"run_id": run_id, "event_name": event_name, "year": year, "kpi_id": "total_posts", "value": float(total)},
        {"run_id": run_id, "event_name": event_name, "year": year, "kpi_id": "valid_posts", "value": float(valid)},
        {"run_id": run_id, "event_name": event_name, "year": year, "kpi_id": "keyword_hit_rate", "value": float(rate)},
    ]


def top_frequency_rows(counter: Counter, key_name: str, top_n: int = 200) -> list[dict]:
    rows: list[dict] = []
    for key, count in counter.most_common(top_n):
        rows.append({key_name: key, "count": int(count)})
    return rows


def _parse_entity_list(value: object) -> list[dict]:
    if value is None:
        return []
    if isinstance(value, list):
        return [x for x in value if isinstance(x, dict)]
    text = str(value).strip()
    if not text:
        return []
    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, list):
            return [x for x in parsed if isinstance(x, dict)]
    except (ValueError, SyntaxError):
        return []
    return []


def _extract_hashtags(row: dict) -> list[str]:
    extracted: list[str] = []
    for h in _parse_entity_list(row.get("raw_hashtags")):
        tag = str(h.get("tag", "")).strip()
        if tag:
            extracted.append(tag)
    if not extracted:
        # Fallback for rows without structured hashtag field.
        extracted.extend(re.findall(r"#([A-Za-z0-9_]+)", str(row.get("normalized_text", ""))))
    return extracted


def _extract_mentions(row: dict) -> list[str]:
    extracted: list[str] = []
    for m in _parse_entity_list(row.get("raw_mentions")):
        username = str(m.get("username", "")).strip()
        if username:
            extracted.append(username)
    if not extracted:
        extracted.extend(re.findall(r"@([A-Za-z0-9_]+)", str(row.get("normalized_text", ""))))
    return extracted
