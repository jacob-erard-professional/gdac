from pathlib import Path
from src.pipeline.config import RunRequest
from src.pipeline.orchestrator import run_pipeline


def test_orchestrator_rejects_missing_stage(tmp_path: Path):
    req = RunRequest(mode='stage', stage=None, year='2024', data_dir=None)
    try:
        run_pipeline(tmp_path, req)
        assert False
    except ValueError:
        assert True
