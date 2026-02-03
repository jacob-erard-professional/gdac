from src.pipeline.contracts import RunManifest, StageResult
from src.pipeline.api_contract_adapter import stage_result_to_contract


def test_contract_adapter_keys():
    m = RunManifest([], [], {'input': 1, 'output': 1}, 'a', 'b')
    payload = stage_result_to_contract(StageResult('ingest', 'success', m))
    assert 'metadata' in payload and 'recordCounts' in payload['metadata']
