from src.common.io.storage import write_text


def run(
    event_name: str,
    year: int,
    kpis: list[dict],
    output_path: str,
    top_hashtags: list[dict] | None = None,
    top_mentions: list[dict] | None = None,
    top_emotions: list[dict] | None = None,
) -> str:
    lines = [f"# {event_name} {year} Summary", "", "## KPI Highlights"]
    for k in kpis:
        lines.append(f"- {k['kpi_id']}: {k['value']}")
    if top_hashtags:
        lines += ["", "## Top Hashtags"]
        for row in top_hashtags[:10]:
            lines.append(f"- #{row['hashtag']}: {row['count']}")
    if top_mentions:
        lines += ["", "## Most Tagged Accounts"]
        for row in top_mentions[:10]:
            lines.append(f"- @{row['mention']}: {row['count']}")
    if top_emotions:
        lines += ["", "## Dominant Emotions"]
        for row in top_emotions[:10]:
            lines.append(f"- {row['emotion']}: {row['count']}")
    write_text(output_path, "\n".join(lines) + "\n")
    return output_path
