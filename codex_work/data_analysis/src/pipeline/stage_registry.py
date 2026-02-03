from src.utils.constants import STAGES


def ordered_stages(include_optional: bool = True):
    if include_optional:
        return STAGES[:]
    return [s for s in STAGES if s not in {"visualize", "export"}]
