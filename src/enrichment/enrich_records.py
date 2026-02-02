def run(rows: list[dict]) -> list[dict]:
    # MVP no-op enrichment: preserve stage boundary and add minimal required field.
    enriched = []
    for row in rows:
        copy = dict(row)
        copy.setdefault("event_phase", "event_day")
        enriched.append(copy)
    return enriched
