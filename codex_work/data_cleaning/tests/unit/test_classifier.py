from src.lib.classifier import classify_batch
from src.models.schemas import TweetRecord


def fake_client(api_key, model, messages, timeout=30, response_format=None, plugins=None):
    return {
        "choices": [
            {
                "message": {
                    "content": '{"results":[{"id":1,"is_about_brand":true,"confidence":0.88,"rationale":"Direct mention"}]}'
                }
            }
        ]
    }


def test_classifier_returns_result():
    tweet = TweetRecord(
        text="I love Angel Soft paper",
        brand="Angel Soft",
        metadata={},
        annotations=[],
        mentions=[],
        hashtags=[],
        cashtags=[],
        urls=[],
        referenced_tweets=[],
        public_metrics={},
    )
    result = classify_batch([tweet], "openrouter/test", "key", fake_client)[0]
    assert result.is_about_brand is True
    assert result.confidence == 0.88
    assert result.rationale == "Direct mention"


def test_classifier_handles_missing_text_or_brand():
    tweet = TweetRecord(
        text="",
        brand="",
        metadata={},
        annotations=[],
        mentions=[],
        hashtags=[],
        cashtags=[],
        urls=[],
        referenced_tweets=[],
        public_metrics={},
    )
    result = classify_batch([tweet], "openrouter/test", "key", fake_client)[0]
    assert result.is_about_brand is False
    assert result.rationale == "Missing text or brand"
