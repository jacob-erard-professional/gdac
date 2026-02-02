import tempfile
import unittest
from pathlib import Path

from src.reporting.generate_narratives import run as run_narratives


class ReportingBundleTests(unittest.TestCase):
    def test_reporting_bundle_files(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            files = run_narratives(
                "super-bowl",
                2025,
                findings=["total_posts: 10"],
                methodology=["config driven"],
                limitations=["sample data"],
                out_dir=td,
            )
            self.assertTrue(Path(files[0]).exists())
            self.assertTrue(Path(files[1]).exists())
