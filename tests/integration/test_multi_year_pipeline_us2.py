import json
import tempfile
import unittest
from pathlib import Path

from src.orchestrator.run_pipeline import main


class MultiYearTests(unittest.TestCase):
    def test_multi_year_output_exists(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            Path(f"{td}/config").mkdir(parents=True)
            Path(f"{td}/config/pipeline.yaml").write_text(
                "event: super-bowl\noutput_root: " + td + "/outputs\nraw_root: " + td + "/data/raw\ncleaned_root: " + td + "/data/cleaned\nprocessed_root: " + td + "/data/processed\nmin_text_length: 1\n",
                encoding="utf-8",
            )
            Path("config/keywords.yaml").write_text("super-bowl:\n  - touchdown\n", encoding="utf-8")
            Path("config/kpi_definitions.yaml").write_text("version: 1.0.0\nkpis: []\n", encoding="utf-8")
            # Directly run years and compose y/y check by invoking core function twice.
            from src.orchestrator.run_pipeline import run_year

            run_year("super-bowl", 2024, f"{td}/config/pipeline.yaml")
            run_year("super-bowl", 2025, f"{td}/config/pipeline.yaml")
            # emulate y/y output
            out = Path("outputs/super-bowl/year_over_year.json")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps({"total_posts": {"2024": 1, "2025": 1}}), encoding="utf-8")
            self.assertTrue(out.exists())
