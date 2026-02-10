from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

from src.brand.agent_executor import AgentExecutionConfig, execute_brand_relevance
from src.brand.agent_schemas import AgentOutput
from src.brand.brand_flags import add_brand_flags
from src.brand.normalize_brand import apply_brand_normalization
from src.brand.output_validation import quarantine_invalid_outputs, validate_outputs
from src.brand.preserve_original import preserve_original_brand
from src.brand.relevance_agent import build_agent_input_payload, current_prompt_hash
from src.brand.relevance_manifest import emit_relevance_manifest
from src.brand.manifest import emit_brand_manifest
from src.cleaning.assemble_clean import assemble_clean_dataset
from src.config.loader import load_config
from src.ingest.column_registry import load_column_registry
from src.ingest.csv_loader import concatenate_datasets, load_csv_files
from src.ingest.manifest import emit_manifest, sha256_file
from src.ingest.quarantine import quarantine_rows
from src.ingest.structural_validation import validate_required_columns, validate_types
from src.text.manifest import emit_text_manifest
from src.text.normalize_text import apply_text_normalization
from src.text.noise_flags import add_noise_flags
from src.text.preserve_original import preserve_original_text
from src.text.url_handling import apply_url_handling
from src.orchestrator.logging import log_event


def run_ingest(config: Dict[str, Any], run_id: str, input_dir: Path, output_dir: Path) -> Tuple[pd.DataFrame, List[Path]]:
    registry_path = Path(config["column_registry_path"])
    registry = load_column_registry(registry_path)
    datasets = load_csv_files(input_dir)
    input_files, df = concatenate_datasets(datasets)

    missing_unknown = registry.validate_input_columns(list(df.columns))
    if missing_unknown["missing"] or missing_unknown["unknown"]:
        log_event("schema_validation", {"missing": missing_unknown["missing"], "unknown": missing_unknown["unknown"]})
        raise ValueError("Input columns do not match registry")

    required_cols = ["id", "text", "brand"]
    valid_mask, reasons = validate_required_columns(df, required_cols)
    type_mask, type_reasons = validate_types(df, required_cols)
    valid_mask = valid_mask & type_mask
    reasons.update(type_reasons)

    missing_id = df["id"].map(lambda v: isinstance(v, str) and v.strip() == "")
    empty_text = df["text"].map(lambda v: isinstance(v, str) and v.strip() == "")
    missing_id_count = int(missing_id.sum())
    empty_text_count = int(empty_text.sum())
    if missing_id_count:
        reasons["missing_id"] = missing_id_count
    if empty_text_count:
        reasons["empty_text"] = empty_text_count
    valid_mask = valid_mask & ~missing_id & ~empty_text

    invalid_mask = ~valid_mask
    rows_rejected = int(invalid_mask.sum())

    quarantine_path = None
    if rows_rejected > 0:
        quarantine_path = quarantine_rows(df, valid_mask, reasons, output_dir / "quarantine")

    df_valid = df[valid_mask].copy()
    output_path = output_dir / "ingested.csv"
    output_dir.mkdir(parents=True, exist_ok=True)
    df_valid.to_csv(output_path, index=False)

    output_files = [output_path]
    if quarantine_path:
        output_files.append(quarantine_path)

    emit_manifest(
        output_path=output_dir / "manifest.json",
        step_name="ingest",
        run_id=run_id,
        input_files=input_files,
        output_files=output_files,
        rows_in=len(df),
        rows_out=len(df_valid),
        rows_rejected=rows_rejected,
        rejection_reasons=reasons,
    )

    log_event("ingest_complete", {"rows_in": len(df), "rows_out": len(df_valid), "rows_rejected": rows_rejected})
    return df_valid, output_files


def run_text_cleaning(
    config: Dict[str, Any],
    run_id: str,
    df: pd.DataFrame,
    output_dir: Path,
    input_files: List[Path],
) -> Tuple[pd.DataFrame, List[Path]]:
    df = preserve_original_text(df)
    df = apply_text_normalization(df, config["text_normalization"]["casing"])
    df = apply_url_handling(df, config["text_normalization"]["url_mode"], config["text_normalization"].get("url_token", "[URL]"))
    df = add_noise_flags(df)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "text_cleaned.csv"
    df.to_csv(output_path, index=False)

    emit_text_manifest(
        output_path=output_dir / "manifest.json",
        run_id=run_id,
        input_files=input_files,
        output_files=[output_path],
        rows_in=len(df),
        rows_out=len(df),
        rows_rejected=0,
        rejection_reasons={},
    )
    log_event("text_cleaning_complete", {"rows_out": len(df)})
    return df, [output_path]


def run_brand_normalization(
    config: Dict[str, Any],
    run_id: str,
    df: pd.DataFrame,
    output_dir: Path,
    input_files: List[Path],
) -> Tuple[pd.DataFrame, List[Path]]:
    df = preserve_original_brand(df)
    df = apply_brand_normalization(df, Path(config["brand_normalization"]["alias_config_path"]))
    df = add_brand_flags(df)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "brand_normalized.csv"
    df.to_csv(output_path, index=False)

    emit_brand_manifest(
        output_path=output_dir / "manifest.json",
        run_id=run_id,
        input_files=input_files,
        output_files=[output_path],
        rows_in=len(df),
        rows_out=len(df),
        rows_rejected=0,
        rejection_reasons={},
    )
    log_event("brand_normalization_complete", {"rows_out": len(df)})
    return df, [output_path]


def run_brand_relevance(
    config: Dict[str, Any],
    run_id: str,
    df: pd.DataFrame,
    output_dir: Path,
    input_files: List[Path],
) -> Tuple[List[AgentOutput], List[Path], pd.DataFrame]:
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = output_dir / "agent_cache"

    rows = []
    agent_inputs_payload = []
    input_ids = []
    for _, row in df.iterrows():
        agent_input, _ = build_agent_input_payload(
            text_normalized=row["text_normalized"],
            brand_normalized=row["brand_normalized"],
            brand_original=row["brand_original"],
            model=config["openrouter"]["model"],
            model_params=config["openrouter"]["model_params"],
        )
        input_ids.append(agent_input.input_id)
        rows.append((row["text_normalized"], row["brand_normalized"], row["brand_original"]))
        agent_inputs_payload.append(agent_input.model_dump())

    df = df.copy()
    df["input_id"] = input_ids

    exec_config = AgentExecutionConfig(
        api_base=config["openrouter"]["api_base"],
        api_key_env=config["openrouter"]["api_key_env"],
        model=config["openrouter"]["model"],
        models=config["openrouter"].get("models"),
        model_params=config["openrouter"]["model_params"],
        timeout_seconds=config["openrouter"]["timeout_seconds"],
        max_retries=config["openrouter"]["max_retries"],
        rate_limit_per_minute=config["openrouter"]["rate_limit_per_minute"],
        cost_ceiling_usd=config["openrouter"]["cost_ceiling_usd"],
        cost_per_call_usd=config["openrouter"].get("cost_per_call_usd", 0.0),
        batch_size=config["openrouter"].get("batch_size", 1),
    )

    outputs_raw, stats = execute_brand_relevance(rows, cache_dir, exec_config)
    valid, invalid = validate_outputs(outputs_raw)

    if invalid:
        quarantine_invalid_outputs(invalid, output_dir)

    inputs_path = output_dir / "agent_inputs.json"
    inputs_path.write_text(json.dumps(agent_inputs_payload, indent=2, sort_keys=True), encoding="utf-8")
    input_hash = sha256_file(inputs_path) if inputs_path.exists() else ""

    output_path = output_dir / "agent_outputs.json"
    output_payload = [o.model_dump() for o in valid]
    output_path.write_text(json.dumps(output_payload, indent=2, sort_keys=True), encoding="utf-8")
    output_hash = sha256_file(output_path) if output_path.exists() else ""

    emit_relevance_manifest(
        output_path=output_dir / "manifest.json",
        run_id=run_id,
        input_files=input_files,
        output_files=[inputs_path, output_path],
        rows_in=len(df),
        rows_out=len(valid),
        rows_rejected=len(invalid),
        rejection_reasons={"invalid_agent_output": len(invalid)} if invalid else {},
        agent_metadata={
            "model": config["openrouter"]["model"],
            "prompt_hash": current_prompt_hash(),
            "input_hash": input_hash,
            "output_hash": output_hash,
        },
    )
    log_event(
        "brand_relevance_complete",
        {
            "rows_out": len(valid),
            "rows_rejected": len(invalid),
            "agent_calls": stats["calls_made"],
            "cache_hits": stats["cached_hits"],
            "estimated_cost_usd": stats["estimated_cost_usd"],
        },
    )
    return valid, [output_path], df


def run_assemble_clean(run_id: str, df: pd.DataFrame, agent_outputs: List[AgentOutput], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    merged = assemble_clean_dataset(df, agent_outputs)
    output_path = output_dir / "clean.csv"
    merged.to_csv(output_path, index=False)
    emit_manifest(
        output_path=output_dir / "manifest.json",
        step_name="assemble_clean",
        run_id=run_id,
        input_files=[],
        output_files=[output_path],
        rows_in=len(df),
        rows_out=len(merged),
        rows_rejected=0,
        rejection_reasons={},
    )
    log_event("assemble_clean_complete", {"rows_out": len(merged)})
    return output_path


def run_pipeline(config_path: Path, year: str, dry_run: bool = False) -> None:
    config = load_config(config_path)
    run_id = str(uuid.uuid4())

    if dry_run:
        log_event("dry_run", {"config": str(config_path), "year": year})
        return

    raw_dir = Path(config["paths"]["raw_base"]) / year
    intermediate_root = Path(config["paths"]["intermediate_base"]) / year
    output_dir = Path(config["paths"]["output_base"]) / year

    ingest_df, ingest_files = run_ingest(config, run_id, raw_dir, intermediate_root / "ingest")
    text_df, text_files = run_text_cleaning(
        config, run_id, ingest_df, intermediate_root / "text", ingest_files
    )
    brand_df, brand_files = run_brand_normalization(
        config, run_id, text_df, intermediate_root / "brand", text_files
    )
    agent_outputs, _, branded_df = run_brand_relevance(
        config, run_id, brand_df, intermediate_root / "relevance", brand_files
    )
    run_assemble_clean(run_id, branded_df, agent_outputs, output_dir)


def run_step(step_name: str, config_path: Path, year: str, dry_run: bool = False) -> None:
    config = load_config(config_path)
    run_id = str(uuid.uuid4())

    if dry_run:
        log_event("dry_run", {"step": step_name, "config": str(config_path), "year": year})
        return

    raw_dir = Path(config["paths"]["raw_base"]) / year
    intermediate_root = Path(config["paths"]["intermediate_base"]) / year
    output_dir = Path(config["paths"]["output_base"]) / year

    if step_name == "ingest":
        run_ingest(config, run_id, raw_dir, intermediate_root / "ingest")
    elif step_name == "text_cleaning":
        input_path = intermediate_root / "ingest" / "ingested.csv"
        df = pd.read_csv(input_path, dtype=str, keep_default_na=False, na_filter=False)
        run_text_cleaning(config, run_id, df, intermediate_root / "text", [input_path])
    elif step_name == "brand_normalization":
        input_path = intermediate_root / "text" / "text_cleaned.csv"
        df = pd.read_csv(input_path, dtype=str, keep_default_na=False, na_filter=False)
        run_brand_normalization(config, run_id, df, intermediate_root / "brand", [input_path])
    elif step_name == "brand_relevance":
        input_path = intermediate_root / "brand" / "brand_normalized.csv"
        df = pd.read_csv(input_path, dtype=str, keep_default_na=False, na_filter=False)
        run_brand_relevance(config, run_id, df, intermediate_root / "relevance", [input_path])
    elif step_name == "assemble_clean":
        input_path = intermediate_root / "brand" / "brand_normalized.csv"
        df = pd.read_csv(input_path, dtype=str, keep_default_na=False, na_filter=False)
        outputs_path = intermediate_root / "relevance" / "agent_outputs.json"
        outputs = [AgentOutput.model_validate(o) for o in json.loads(outputs_path.read_text(encoding="utf-8"))]
        run_assemble_clean(run_id, df, outputs, output_dir)
    else:
        raise ValueError(f"Unknown step: {step_name}")
