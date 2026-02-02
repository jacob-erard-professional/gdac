#!/usr/bin/env bash
set -euo pipefail
python3 -m src.orchestrator.run_pipeline --event super-bowl --year 2025 --config config/pipeline.yaml
