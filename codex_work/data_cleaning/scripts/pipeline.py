from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from src.orchestrator.pipeline import run_pipeline, run_step


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deterministic data cleaning pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    run_cmd = sub.add_parser("run", help="Run full pipeline")
    run_cmd.add_argument("--config", required=True)
    run_cmd.add_argument("--year", required=True)
    run_cmd.add_argument("--dry-run", action="store_true")

    step_cmd = sub.add_parser("step", help="Run a single step")
    step_cmd.add_argument("--name", required=True)
    step_cmd.add_argument("--config", required=True)
    step_cmd.add_argument("--year", required=True)
    step_cmd.add_argument("--dry-run", action="store_true")

    validate_cmd = sub.add_parser("validate", help="Validation-only mode")
    validate_cmd.add_argument("--config", required=True)
    validate_cmd.add_argument("--year", required=True)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "run":
        run_pipeline(Path(args.config), args.year, dry_run=args.dry_run)
    elif args.command == "step":
        run_step(args.name, Path(args.config), args.year, dry_run=args.dry_run)
    elif args.command == "validate":
        run_step("ingest", Path(args.config), args.year, dry_run=False)


if __name__ == "__main__":
    main()
