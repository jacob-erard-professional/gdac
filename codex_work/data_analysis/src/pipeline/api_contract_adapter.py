from .contracts import StageResult


def stage_result_to_contract(result: StageResult) -> dict:
    return {
        "stage": result.stage,
        "status": result.status,
        "metadata": {
            "inputFiles": result.metadata.input_files,
            "outputFiles": result.metadata.output_files,
            "recordCounts": result.metadata.record_counts,
            "startedAt": result.metadata.started_at,
            "completedAt": result.metadata.completed_at,
            "notes": result.metadata.notes,
        },
    }
