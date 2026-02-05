from src.pipeline.contracts import RunManifest, StageResult
from src.pipeline.api_contract_adapter import stage_result_to_contract


def test_contract_adapter_keys():
    m = RunManifest([], [], {'input': 1, 'output': 1}, 'a', 'b')
    payload = stage_result_to_contract(StageResult('ingest', 'success', m))
    assert 'metadata' in payload and 'recordCounts' in payload['metadata']


def test_contract_adapter_accepts_deep_sentiment_stage():
    m = RunManifest([], [], {'input': 2, 'output': 2}, 'a', 'b', notes=['model_id=test'])
    payload = stage_result_to_contract(StageResult('deep_sentiment', 'success', m))
    assert payload['stage'] == 'deep_sentiment'
    assert payload['metadata']['recordCounts']['output'] == 2
