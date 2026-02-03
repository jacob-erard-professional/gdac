from src.analytics.registry import module_registry


def test_registry_contains_modules():
    m = module_registry()
    assert set(m.keys()) == {'hashtags_frequency', 'mentions_frequency'}
