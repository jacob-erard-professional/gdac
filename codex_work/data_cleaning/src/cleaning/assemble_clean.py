from __future__ import annotations

from typing import List

import pandas as pd

from src.brand.agent_schemas import AgentOutput


def assemble_clean_dataset(df: pd.DataFrame, agent_outputs: List[AgentOutput]) -> pd.DataFrame:
    outputs_df = pd.DataFrame([o.model_dump() for o in agent_outputs])
    merged = df.merge(outputs_df, on="input_id", how="left")
    return merged
