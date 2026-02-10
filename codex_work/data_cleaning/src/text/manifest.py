from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from src.ingest.manifest import emit_manifest


def emit_text_manifest(
    output_path: Path,
    run_id: str,
    input_files: List[Path],
    output_files: List[Path],
    rows_in: int,
    rows_out: int,
    rows_rejected: int,
    rejection_reasons: Dict[str, int],
) -> Path:
    return emit_manifest(
        output_path=output_path,
        step_name="text_cleaning",
        run_id=run_id,
        input_files=input_files,
        output_files=output_files,
        rows_in=rows_in,
        rows_out=rows_out,
        rows_rejected=rows_rejected,
        rejection_reasons=rejection_reasons,
    )
