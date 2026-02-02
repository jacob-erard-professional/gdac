from src.common.io.storage import write_json


def build_traceability(kpis: list[dict], claims: list[str], output_path: str) -> str:
    mapping = []
    kpi_ids = [k["kpi_id"] for k in kpis]
    for claim in claims:
        mapping.append({"claim": claim, "kpi_ids": kpi_ids})
    write_json(output_path, {"traceability": mapping})
    return output_path
