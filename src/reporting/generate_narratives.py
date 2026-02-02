from src.common.io.storage import write_text


def run(event_name: str, year: int, findings: list[str], methodology: list[str], limitations: list[str], out_dir: str) -> list[str]:
    wp = f"{out_dir}/white_paper_summary.md"
    ex = f"{out_dir}/executive_summary.md"
    write_text(
        wp,
        "\n".join(
            [
                f"# White Paper Summary: {event_name} {year}",
                "",
                "## Methodology",
                *[f"- {m}" for m in methodology],
                "",
                "## Findings",
                *[f"- {f}" for f in findings],
                "",
                "## Limitations",
                *[f"- {l}" for l in limitations],
                "",
            ]
        ),
    )
    write_text(
        ex,
        "\n".join(
            [
                f"# Executive Brief: {event_name} {year}",
                "",
                "## Top Findings",
                *[f"- {f}" for f in findings],
                "",
                "## Caveats",
                *[f"- {l}" for l in limitations],
                "",
            ]
        ),
    )
    return [wp, ex]
