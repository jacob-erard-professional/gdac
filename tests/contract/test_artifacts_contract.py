import unittest
from pathlib import Path


class ArtifactContractTests(unittest.TestCase):
    def test_openapi_has_artifacts_endpoint(self) -> None:
        text = Path("specs/001-build-superbowl-analytics-pipeline/contracts/pipeline-orchestrator.openapi.yaml").read_text(encoding="utf-8")
        self.assertIn("/runs/{run_id}/artifacts", text)
