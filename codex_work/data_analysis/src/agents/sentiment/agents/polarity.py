from src.agents.sentiment.prompts import POLARITY_PROMPT
from src.agents.sentiment.schemas.agent_outputs import PolarityOutput


def run_polarity(text: str, llm_client=None) -> PolarityOutput:
    if llm_client is None:
        t = text.lower()
        if any(w in t for w in ["love", "great", "win", "awesome", "good"]):
            return PolarityOutput(sentiment="positive", confidence=0.72, rationale="heuristic positive cue")
        if any(w in t for w in ["bad", "hate", "lose", "awful", "terrible"]):
            return PolarityOutput(sentiment="negative", confidence=0.72, rationale="heuristic negative cue")
        return PolarityOutput(sentiment="neutral", confidence=0.6, rationale="no strong polarity cue")

    payload = llm_client.invoke_json(f"{POLARITY_PROMPT}\ntext={text!r}")
    return PolarityOutput.model_validate(payload)

