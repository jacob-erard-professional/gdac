from src.common.io.storage import write_text


def run(kpi_rows: list[dict], visual_dir: str) -> list[str]:
    lines = ["kpi_id,value"]
    for row in kpi_rows:
        lines.append(f"{row['kpi_id']},{row['value']}")
    csv_path = f"{visual_dir}/kpi_chart_data.csv"
    txt_path = f"{visual_dir}/kpi_summary.txt"
    write_text(csv_path, "\n".join(lines) + "\n")
    write_text(txt_path, "\n".join(lines[1:]) + "\n")
    return [csv_path, txt_path]
