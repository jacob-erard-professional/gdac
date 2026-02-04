from dataclasses import dataclass
from pathlib import Path
from src.pipeline.config import RunRequest
from src.pipeline.path_resolution import resolve_year_config
from src.pipeline.stage_registry import ordered_stages
from src.pipeline.contracts import StageResult
from src.pipeline.year_discovery import discover_years
from src.pipeline import stages
from src.pipeline.api_contract_adapter import stage_result_to_contract
from src.utils.guards import ensure_not_raw_output


RUNNERS = {
    'ingest': stages.ingest.run,
    'clean': stages.clean.run,
    'process': stages.process.run,
    'analyze': stages.analyze.run,
    'visualize': stages.visualize.run,
    'export': stages.export.run,
}


@dataclass
class OrchestratorResult:
    year: str
    mode: str
    status: str
    stages: list[dict]


def _run_for_year(
    base_dir: Path,
    req: RunRequest,
    year: str | None,
    data_dir: Path | None,
    stage_list: list[str],
):
    config = resolve_year_config(base_dir, year=year, data_dir=data_dir)
    results = []
    for stage in stage_list:
        manifest = RUNNERS[stage](config)
        for out in manifest.output_files:
            ensure_not_raw_output(Path(out))
        stage_result = StageResult(stage=stage, status='success', metadata=manifest)
        results.append(stage_result_to_contract(stage_result))
    return OrchestratorResult(year=year, mode=req.mode, status='success', stages=results)


def run_pipeline(base_dir: Path, req: RunRequest):
    if req.mode == 'stage':
        if not req.stage:
            raise ValueError('stage mode requires stage')
        stage_list = [req.stage]
        if bool(req.year) == bool(req.data_dir):
            raise ValueError('stage mode requires year or data_dir')
        return [_run_for_year(base_dir, req, req.year, req.data_dir, stage_list)]

    if req.mode == 'full_year':
        if bool(req.year) == bool(req.data_dir):
            raise ValueError('full_year mode requires year or data_dir')
        stage_list = ordered_stages(include_optional=False)
        return [_run_for_year(base_dir, req, req.year, req.data_dir, stage_list)]

    if req.mode == 'full_all_years':
        years = discover_years(base_dir / 'data' / 'raw')
        stage_list = ordered_stages(include_optional=False)
        return [
            _run_for_year(base_dir, req, y, None, stage_list)
            for y in years
        ]

    raise ValueError(f'unknown mode {req.mode}')
