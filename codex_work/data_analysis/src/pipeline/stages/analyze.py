"""Pipeline module for analyze orchestration and execution."""

import csv
from src.analytics.registry import module_registry
from src.pipeline.stage_runtime import make_manifest


def run(config, *, clean_outputs: bool = False):
    in_file = config.enriched_dir / 'enriched.csv'
    with in_file.open(newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    out_dir = config.analytics_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    if clean_outputs:
        for existing in out_dir.glob('*'):
            if existing.is_file():
                existing.unlink()
    outputs = []
    for _, func in module_registry().items():
        outputs.append(func(rows, config.year, out_dir))
    return make_manifest([in_file], outputs, len(rows), len(rows))
