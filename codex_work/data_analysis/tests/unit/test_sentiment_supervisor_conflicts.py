from src.agents.sentiment.schemas.agent_outputs import EmotionOutput, PolarityOutput, SarcasmOutput
from src.agents.sentiment.supervisor.supervisor import adjudicate_final


def test_supervisor_downshifts_when_sarcasm_is_high():
    polarity = PolarityOutput(sentiment="positive", confidence=0.9, rationale="x")
    emotion = EmotionOutput(emotion="joy", confidence=0.8, rationale="x")
    sarcasm = SarcasmOutput(is_sarcastic=True, confidence=0.8, rationale="x")

    final, flags = adjudicate_final(polarity=polarity, emotion=emotion, sarcasm=sarcasm)

    assert final.sentiment == "neutral"
    assert "sarcasm_risk" in flags
