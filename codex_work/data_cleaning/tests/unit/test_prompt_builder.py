from src.lib.prompt_builder import build_messages_batch
from src.models.schemas import TweetRecord


def test_build_messages_includes_text_brand_and_context():
    tweet = TweetRecord(
        text="Love Angel Soft",
        brand="Angel Soft",
        metadata={"username": "user1", "name": "User One"},
        annotations=[{"normalized_text": "Angel soft"}],
        mentions=[],
        hashtags=[],
        cashtags=[],
        urls=[],
        referenced_tweets=[],
        public_metrics={},
    )

    messages = build_messages_batch([tweet])
    assert messages[0]["role"] == "system"
    content = messages[1]["content"]
    assert "TOON INPUT" in content
    assert "Angel Soft" in content
    assert "Love Angel Soft" in content
