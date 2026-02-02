from src.common.io.storage import file_sha256, write_json


def write_artifact_index(path: str, artifacts: list[dict]) -> None:
    for artifact in artifacts:
        fp = artifact.get("file_path")
        artifact["checksum"] = file_sha256(fp) if fp else ""
    write_json(path, artifacts)
