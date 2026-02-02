import unittest

from src.orchestrator.schema_guard import ensure_kpi_schema


class StageValidationTests(unittest.TestCase):
    def test_kpi_schema_valid(self) -> None:
        rows = [{"run_id": "r", "event_name": "e", "year": 2025, "kpi_id": "k", "value": 1.0}]
        ensure_kpi_schema(rows)

    def test_kpi_schema_missing_field(self) -> None:
        with self.assertRaises(ValueError):
            ensure_kpi_schema([{"event_name": "e"}])
