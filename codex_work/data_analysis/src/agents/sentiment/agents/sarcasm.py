from src.agents.sentiment.prompts import SARCASM_PROMPT
from src.agents.sentiment.schemas.agent_outputs import SarcasmOutput


def run_sarcasm(text: str, llm_client=None) -> SarcasmOutput:
    if llm_client is None:
        t = text.lower()
        cue = any(w in t for w in ["yeah right", "sure", "totally", "/s"])
        return SarcasmOutput(
            is_sarcastic=cue,
            confidence=0.62 if cue else 0.55,
            rationale="heuristic sarcasm cue" if cue else "no sarcasm cue",
        )

    payload = llm_client.invoke_json(f"{SARCASM_PROMPT}\ntext={text!r}")
    return SarcasmOutput.model_validate(payload)

