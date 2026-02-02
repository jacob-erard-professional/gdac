import json
import tempfile
import unittest
from pathlib import Path

from src.common.io.storage import ensure_dir, write_json
from src.common.logging.structured_logger import write_json_log
from src.common.schemas.entities import PipelineRun


class FoundationTests(unittest.TestCase):
    def test_storage_and_logging(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ensure_dir(f"{td}/a/b")
            write_json(f"{td}/a/b/x.json", {"ok": True})
            self.assertTrue(Path(f"{td}/a/b/x.json").exists())

            log_path = f"{td}/run.log.jsonl"
            write_json_log(log_path, "INFO", "hello", run_id="1")
            line = Path(log_path).read_text(encoding="utf-8").strip()
            payload = json.loads(line)
            self.assertEqual(payload["message"], "hello")

    def test_schema_instantiation(self) -> None:
        run = PipelineRun(run_id="r1", event_name="super-bowl", year=2025, status="running")
        self.assertEqual(run.year, 2025)
