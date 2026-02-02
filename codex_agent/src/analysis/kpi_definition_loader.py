import yaml


def load_kpi_definitions(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        payload = yaml.safe_load(f) or {}
    return payload
