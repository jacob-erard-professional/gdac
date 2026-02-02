from src.common.io.storage import write_json


def run(visual_paths: list[str], export_path: str) -> str:
    write_json(export_path, {"assets": visual_paths})
    return export_path
