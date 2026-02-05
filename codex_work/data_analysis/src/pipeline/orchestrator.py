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
    'sentiment': stages.sentiment.run,
    'ad_sentiment': stages.ad_sentiment.run,
    'deep_sentiment': stages.deep_sentiment.run,
}


@dataclass
class OrchestratorResult:
    year: str
    mode: str
    status: str
    stages: list[dict]


def _log(message: str) -> None:
    print(f"[pipeline] {message}")


def _run_for_year(
    base_dir: Path,
    req: RunRequest,
    year: str | None,
    data_dir: Path | None,
    stage_list: list[str],
):
    config = resolve_year_config(base_dir, year=year, data_dir=data_dir)
    _log(f"year={config.year} mode={req.mode} starting")
    results = []
    total_stages = len(stage_list)
    for idx, stage in enumerate(stage_list, start=1):
        _log(f"year={config.year} stage={stage} ({idx}/{total_stages}) start")
        if stage == 'sentiment':
            manifest = RUNNERS[stage](
                config,
                model_id=req.sentiment_model,
                batch_size=req.sentiment_batch_size,
                dry_run=req.sentiment_dry_run,
                allow_fallback=req.sentiment_allow_fallback,
            )
        elif stage == 'ad_sentiment':
            manifest = RUNNERS[stage](
                config,
                min_tweets=req.ad_sentiment_min_tweets,
            )
        elif stage == 'deep_sentiment':
            manifest = RUNNERS[stage](
                config,
                model_id=req.deep_sentiment_model,
                batch_size=req.deep_sentiment_batch_size,
                dry_run=req.deep_sentiment_dry_run,
                label_map_file=req.deep_sentiment_label_map_file,
            )
        else:
            manifest = RUNNERS[stage](config)
        for out in manifest.output_files:
            ensure_not_raw_output(Path(out))
        stage_result = StageResult(stage=stage, status='success', metadata=manifest)
        results.append(stage_result_to_contract(stage_result))
        _log(
            f"year={config.year} stage={stage} complete "
            f"rows_in={manifest.record_counts['input']} rows_out={manifest.record_counts['output']}"
        )
    _log(f"year={config.year} mode={req.mode} complete")
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
        if req.with_sentiment:
            stage_list = stage_list + ['sentiment']
        if req.with_ad_sentiment:
            stage_list = stage_list + ['ad_sentiment']
        if req.with_deep_sentiment:
            stage_list = stage_list + ['deep_sentiment']
        return [_run_for_year(base_dir, req, req.year, req.data_dir, stage_list)]

    if req.mode == 'full_all_years':
        years = discover_years(base_dir / 'data' / 'raw')
        stage_list = ordered_stages(include_optional=False)
        if req.with_sentiment:
            stage_list = stage_list + ['sentiment']
        if req.with_ad_sentiment:
            stage_list = stage_list + ['ad_sentiment']
        if req.with_deep_sentiment:
            stage_list = stage_list + ['deep_sentiment']
        return [
            _run_for_year(base_dir, req, y, None, stage_list)
            for y in years
        ]

    raise ValueError(f'unknown mode {req.mode}')
