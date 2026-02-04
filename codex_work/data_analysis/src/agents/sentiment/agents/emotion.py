from src.agents.sentiment.prompts import EMOTION_PROMPT
from src.agents.sentiment.schemas.agent_outputs import EmotionOutput


def run_emotion(text: str, llm_client=None) -> EmotionOutput:
    if llm_client is None:
        t = text.lower()
        if any(w in t for w in ["yay", "love", "great", "happy"]):
            return EmotionOutput(emotion="joy", confidence=0.68, rationale="joy cues")
        if any(w in t for w in ["wow", "omg", "hype", "excited"]):
            return EmotionOutput(emotion="excitement", confidence=0.64, rationale="excitement cues")
        if any(w in t for w in ["angry", "mad", "furious"]):
            return EmotionOutput(emotion="anger", confidence=0.66, rationale="anger cues")
        if any(w in t for w in ["sad", "disappointed", "letdown"]):
            return EmotionOutput(emotion="disappointment", confidence=0.66, rationale="disappointment cues")
        return EmotionOutput(emotion="neutral", confidence=0.58, rationale="no strong emotion cue")

    payload = llm_client.invoke_json(f"{EMOTION_PROMPT}\ntext={text!r}")
    return EmotionOutput.model_validate(payload)

