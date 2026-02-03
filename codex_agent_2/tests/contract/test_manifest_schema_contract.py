from __future__ import annotations

import json

import pytest

from src.artifacts.schemas.manifest import PipelineManifest
from src.artifacts.validator import validate_manifest_payload


def test_valid_manifest_contract_roundtrip():
    manifest = PipelineManifest()
    payload = manifest.model_dump_json()
    parsed = validate_manifest_payload(payload)
    assert parsed.manifest_version == "1.0.0"


def test_invalid_manifest_returns_machine_readable_error():
    bad_payload = json.dumps({"pipeline_name": "x"})
    with pytest.raises(ValueError) as exc:
        validate_manifest_payload(bad_payload)
    err = exc.value.args[0]
    assert err["code"] == "SCHEMA_MISMATCH"
    assert "details" in err
