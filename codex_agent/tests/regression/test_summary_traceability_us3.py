import json
import tempfile
import unittest
from pathlib import Path

from src.reporting.traceability import build_traceability


class TraceabilityTests(unittest.TestCase):
    def test_traceability_links_claims_to_kpis(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = build_traceability(
                [{"kpi_id": "total_posts"}],
                ["Claim A"],
                f"{td}/traceability.json",
            )
            payload = json.loads(Path(out).read_text(encoding="utf-8"))
            self.assertEqual(payload["traceability"][0]["kpi_ids"], ["total_posts"])
