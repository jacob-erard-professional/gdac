import json
import tempfile
import unittest
from pathlib import Path

from src.orchestrator.run_pipeline import run_year


class CliManifestContractTests(unittest.TestCase):
    def test_manifest_and_artifact_index_schema(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            Path(f"{td}/config").mkdir(parents=True)
            Path(f"{td}/config/pipeline.yaml").write_text(
                "event: super-bowl\noutput_root: " + td + "/outputs\nraw_root: " + td + "/data/raw\ncleaned_root: " + td + "/data/cleaned\nprocessed_root: " + td + "/data/processed\nmin_text_length: 1\n",
                encoding="utf-8",
            )
            Path("config/keywords.yaml").write_text("super-bowl:\n  - touchdown\n", encoding="utf-8")
            Path("config/kpi_definitions.yaml").write_text("version: 1.0.0\nkpis: []\n", encoding="utf-8")
            result = run_year("super-bowl", 2025, f"{td}/config/pipeline.yaml")
            manifest = json.loads(Path(result["manifest_path"]).read_text(encoding="utf-8"))
            self.assertIn("run_id", manifest)
            self.assertIn("artifact_index", manifest)
            index = json.loads(Path(result["artifact_index"]).read_text(encoding="utf-8"))
            self.assertIsInstance(index, list)
            self.assertTrue(all("artifact_type" in x and "file_path" in x for x in index))
