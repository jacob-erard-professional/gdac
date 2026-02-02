import json
import tempfile
import unittest
from pathlib import Path

from src.orchestrator.run_pipeline import run_year


class DeterminismTests(unittest.TestCase):
    def test_rerun_produces_same_kpi_values(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            Path(f"{td}/config").mkdir(parents=True)
            Path(f"{td}/config/pipeline.yaml").write_text(
                "event: super-bowl\noutput_root: " + td + "/outputs\nraw_root: " + td + "/data/raw\ncleaned_root: " + td + "/data/cleaned\nprocessed_root: " + td + "/data/processed\nmin_text_length: 1\n",
                encoding="utf-8",
            )
            Path("config/keywords.yaml").write_text("super-bowl:\n  - touchdown\n", encoding="utf-8")
            Path("config/kpi_definitions.yaml").write_text("version: 1.0.0\nkpis: []\n", encoding="utf-8")
            a = run_year("super-bowl", 2025, f"{td}/config/pipeline.yaml")
            b = run_year("super-bowl", 2025, f"{td}/config/pipeline.yaml")
            akpi = Path(a["manifest_path"]).parent.parent / "kpis" / "kpis.json"
            bkpi = Path(b["manifest_path"]).parent.parent / "kpis" / "kpis.json"
            self.assertEqual(json.loads(akpi.read_text(encoding="utf-8")), json.loads(bkpi.read_text(encoding="utf-8")))
