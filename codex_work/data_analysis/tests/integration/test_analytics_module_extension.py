from src.analytics.registry import module_registry


def test_registry_contains_modules():
    m = module_registry()
    assert 'volume' in m and 'text_network' in m
