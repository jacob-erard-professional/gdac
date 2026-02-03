from src.pipeline.stages.process import _sentiment


def test_sentiment_rules():
    assert _sentiment('I love this') == 'positive'
    assert _sentiment('I hate this') == 'negative'
    assert _sentiment('This is text') == 'neutral'
