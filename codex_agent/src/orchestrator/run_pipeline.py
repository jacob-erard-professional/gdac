import hashlib
import json
import uuid
import csv
import time
from pathlib import Path

import yaml

from src.analysis.compute_kpis import (
    finalize_accumulator,
    init_accumulator,
    top_frequency_rows,
    update_accumulator,
)
from src.analysis.kpi_definition_loader import load_kpi_definitions
from src.analysis.nlp_agent import NLPAggregator
from src.analysis.nlp_ml_agent import EmotionMLAgent
from src.analysis.build_year_over_year_views import build_year_over_year
from src.analysis.brand_analytics import BrandAggregator
from src.cleaning.clean_records import run as run_cleaning
from src.common.io.storage import append_jsonl, ensure_dir, write_json, write_jsonl
from src.common.logging.structured_logger import write_json_log
from src.enrichment.enrich_records import run as run_enrichment
from src.ingestion.ingest_x_data import iter_chunks
from src.orchestrator.artifact_writer import write_artifact_index
from src.orchestrator.cli import parse_args
from src.orchestrator.determinism import seed_random, stable_sort_records
from src.orchestrator.manifest import write_manifest
from src.orchestrator.quality_reporting import summarize_quality
from src.orchestrator.schema_guard import ensure_kpi_schema
from src.reporting.generate_narratives import run as run_narratives
from src.reporting.generate_summary import run as run_summary
from src.reporting.traceability import build_traceability
from src.visualization.export_infographic_assets import run as export_infographic_assets
from src.visualization.generate_visuals import run as run_visuals


def _load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _config_hash(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _rows_to_ad_emotion_map(rows: list[dict]) -> dict[tuple[str, str], dict]:
    out: dict[tuple[str, str], dict] = {}
    for row in rows:
        key = (str(row.get("brand_ad_name", "UNKNOWN_AD")), str(row.get("emotion", "")))
        out[key] = row
    return out


def _write_roi_join_ready(
    path: str,
    *,
    event: str,
    year: int,
    lex_rows: list[dict],
    ml_rows: list[dict],
) -> None:
    lex_map = _rows_to_ad_emotion_map(lex_rows)
    ml_map = _rows_to_ad_emotion_map(ml_rows)
    keys = sorted(set(lex_map.keys()) | set(ml_map.keys()))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "event_name",
                "year",
                "brand_ad_name",
                "emotion",
                "lexicon_count",
                "lexicon_share_within_ad",
                "ml_count",
                "ml_share_within_ad",
                "roi",
                "ad_spend",
                "notes",
            ],
        )
        writer.writeheader()
        for ad_name, emotion in keys:
            lex = lex_map.get((ad_name, emotion), {})
            ml = ml_map.get((ad_name, emotion), {})
            writer.writerow(
                {
                    "event_name": event,
                    "year": year,
                    "brand_ad_name": ad_name,
                    "emotion": emotion,
                    "lexicon_count": int(lex.get("count", 0)),
                    "lexicon_share_within_ad": float(lex.get("share_within_ad", 0.0)),
                    "ml_count": int(ml.get("count", 0)),
                    "ml_share_within_ad": float(ml.get("share_within_ad", 0.0)),
                    "roi": "",
                    "ad_spend": "",
                    "notes": "",
                }
            )


def run_year(event: str, year: int, config_path: str) -> dict:
    run_started_at = time.perf_counter()
    seed_random(year)
    cfg = _load_yaml(config_path)
    raw_root = cfg.get("raw_root", "data/raw")
    cleaned_root = cfg.get("cleaned_root", "data/cleaned")
    processed_root = cfg.get("processed_root", "data/processed")
    output_root = cfg.get("output_root", "outputs")
    min_text_length = int(cfg.get("min_text_length", 3))
    input_format = str(cfg.get("input_format", "jsonl")).lower()
    chunk_size = int(cfg.get("chunk_size", 100_000))
    csv_delimiter = str(cfg.get("csv_delimiter", ","))
    csv_encoding = str(cfg.get("csv_encoding", "utf-8"))
    csv_columns = cfg.get("csv_columns", {})
    eda_top_n = int(cfg.get("eda_top_n", 500))
    nlp_similarity_threshold = float(cfg.get("nlp_similarity_threshold", 0.72))
    nlp_sample_limit = int(cfg.get("nlp_sample_limit", 20))
    nlp_min_confidence = float(cfg.get("nlp_min_confidence", 0.45))
    nlp_min_margin = float(cfg.get("nlp_min_margin", 0.10))
    nlp_min_training_rows = int(cfg.get("nlp_min_training_rows", 200))
    brand_typo_similarity_threshold = float(cfg.get("brand_typo_similarity_threshold", 0.87))
    brand_top_n = int(cfg.get("brand_top_n", 300))
    progress_every_chunks = int(cfg.get("progress_every_chunks", 10))
    progress_every_rows = int(cfg.get("progress_every_rows", max(chunk_size, 250_000)))

    run_id = str(uuid.uuid4())
    cleaned_path = f"{cleaned_root}/{event}/{year}/cleaned.jsonl"
    processed_path = f"{processed_root}/{event}/{year}/enriched.jsonl"

    out_dir = f"{output_root}/{event}/{year}"
    kpi_dir = f"{out_dir}/kpis"
    visual_dir = f"{out_dir}/visuals"
    summary_dir = f"{out_dir}/summaries"
    manifest_dir = f"{out_dir}/manifests"

    for d in [kpi_dir, visual_dir, summary_dir, manifest_dir, f"{raw_root}/{event}/{year}"]:
        ensure_dir(d)

    log_path = f"{manifest_dir}/run.log.jsonl"
    write_json_log(log_path, "INFO", "run_started", run_id=run_id, event=event, year=year)
    print(f"[run] start event={event} year={year} format={input_format} run_id={run_id}")

    keywords_cfg = _load_yaml("config/keywords.yaml")
    keywords = keywords_cfg.get(event, [])
    kpi_acc = init_accumulator(keywords)
    nlp_lexicon = NLPAggregator(
        top_n=eda_top_n,
        similarity_threshold=nlp_similarity_threshold,
        sample_limit=nlp_sample_limit,
    )
    nlp_ml = EmotionMLAgent(
        top_n=eda_top_n,
        similarity_threshold=nlp_similarity_threshold,
        sample_limit=nlp_sample_limit,
        min_confidence=nlp_min_confidence,
        min_margin=nlp_min_margin,
        min_training_rows=nlp_min_training_rows,
    )
    brands = BrandAggregator(typo_similarity_threshold=brand_typo_similarity_threshold)
    total_cleaning_report = {"accepted": 0, "rejected": 0, "rejection_breakdown": {}}
    total_raw_rows = 0
    chunk_count = 0
    stage_seconds: dict[str, float] = {}

    def _time_stage(name: str, fn):
        start = time.perf_counter()
        value = fn()
        stage_seconds[name] = stage_seconds.get(name, 0.0) + (time.perf_counter() - start)
        return value

    # Truncate staged outputs for deterministic reruns.
    ensure_dir(Path(cleaned_path).parent.as_posix())
    ensure_dir(Path(processed_path).parent.as_posix())
    Path(cleaned_path).write_text("", encoding="utf-8")
    Path(processed_path).write_text("", encoding="utf-8")

    for raw_rows in iter_chunks(
        raw_root=raw_root,
        event_name=event,
        year=year,
        input_format=input_format,
        chunk_size=chunk_size,
        csv_delimiter=csv_delimiter,
        csv_encoding=csv_encoding,
        csv_columns=csv_columns,
    ):
        chunk_count += 1
        total_raw_rows += len(raw_rows)
        raw_rows = _time_stage("sort_rows", lambda: stable_sort_records(raw_rows))
        cleaned_rows, cleaning_report = _time_stage(
            "cleaning",
            lambda: run_cleaning(raw_rows, min_text_length=min_text_length),
        )
        enriched_rows = _time_stage("enrichment", lambda: run_enrichment(cleaned_rows))
        append_jsonl(cleaned_path, cleaned_rows)
        append_jsonl(processed_path, enriched_rows)
        update_accumulator(kpi_acc, enriched_rows)
        nlp_lexicon.update(enriched_rows)
        nlp_ml.update(enriched_rows)
        brands.update(enriched_rows)
        total_cleaning_report["accepted"] += cleaning_report.get("accepted", 0)
        total_cleaning_report["rejected"] += cleaning_report.get("rejected", 0)
        for key, value in cleaning_report.get("rejection_breakdown", {}).items():
            total_cleaning_report["rejection_breakdown"][key] = (
            total_cleaning_report["rejection_breakdown"].get(key, 0) + value
            )
        if (
            (progress_every_chunks > 0 and chunk_count % progress_every_chunks == 0)
            or (progress_every_rows > 0 and total_raw_rows % progress_every_rows < len(raw_rows))
        ):
            print(
                f"[run] progress year={year} chunks={chunk_count} raw_rows={total_raw_rows} "
                f"accepted={total_cleaning_report['accepted']} rejected={total_cleaning_report['rejected']}"
            )

    if total_raw_rows <= 2:
        print(
            "[warn] Very low raw row count detected. Check input_format, raw file path, and csv_columns mapping."
        )

    kpi_rows = _time_stage("kpi_finalize", lambda: finalize_accumulator(kpi_acc, run_id, event, year))
    ensure_kpi_schema(kpi_rows)

    kpi_file = f"{kpi_dir}/kpis.json"
    write_json(kpi_file, {"kpis": kpi_rows})
    hashtag_freq_file = f"{kpi_dir}/hashtag_frequencies.jsonl"
    mention_freq_file = f"{kpi_dir}/mention_frequencies.jsonl"
    lex_dir = f"{kpi_dir}/nlp_lexicon"
    ml_dir = f"{kpi_dir}/nlp_ml"
    ensure_dir(lex_dir)
    ensure_dir(ml_dir)
    lex_emotion_by_ad_file = f"{lex_dir}/emotion_by_ad.jsonl"
    lex_emotion_examples_file = f"{lex_dir}/emotion_examples.jsonl"
    lex_similar_hashtags_file = f"{lex_dir}/similar_hashtags.jsonl"
    lex_emotion_overview_file = f"{lex_dir}/emotion_overview.json"
    ml_emotion_by_ad_file = f"{ml_dir}/emotion_by_ad.jsonl"
    ml_emotion_examples_file = f"{ml_dir}/emotion_examples.jsonl"
    ml_similar_hashtags_file = f"{ml_dir}/similar_hashtags.jsonl"
    ml_emotion_overview_file = f"{ml_dir}/emotion_overview.json"
    roi_join_ready_file = f"{kpi_dir}/roi_join_ready.csv"
    brand_popularity_file = f"{kpi_dir}/brand_popularity.jsonl"
    hashtag_rows = top_frequency_rows(kpi_acc["hashtag_counts"], "hashtag", top_n=eda_top_n)
    mention_rows = top_frequency_rows(kpi_acc["mention_counts"], "mention", top_n=eda_top_n)
    lex_outputs = _time_stage("nlp_lexicon_finalize", lambda: nlp_lexicon.finalize())
    ml_outputs = _time_stage("nlp_ml_finalize", lambda: nlp_ml.finalize())
    write_jsonl(hashtag_freq_file, hashtag_rows)
    write_jsonl(mention_freq_file, mention_rows)
    write_jsonl(lex_emotion_by_ad_file, lex_outputs.emotion_by_ad_rows)
    write_jsonl(lex_emotion_examples_file, lex_outputs.emotion_examples_rows)
    write_jsonl(lex_similar_hashtags_file, lex_outputs.hashtag_similarity_rows)
    write_json(lex_emotion_overview_file, {"emotion_counts": lex_outputs.emotion_counts, "model_mode": lex_outputs.model_mode})
    write_jsonl(ml_emotion_by_ad_file, ml_outputs.emotion_by_ad_rows)
    write_jsonl(ml_emotion_examples_file, ml_outputs.emotion_examples_rows)
    write_jsonl(ml_similar_hashtags_file, ml_outputs.hashtag_similarity_rows)
    write_json(ml_emotion_overview_file, {"emotion_counts": ml_outputs.emotion_counts, "model_mode": ml_outputs.model_mode})
    brand_rows = _time_stage("brand_finalize", lambda: brands.finalize(top_n=brand_top_n))
    write_jsonl(brand_popularity_file, brand_rows)
    _write_roi_join_ready(
        roi_join_ready_file,
        event=event,
        year=year,
        lex_rows=lex_outputs.emotion_by_ad_rows,
        ml_rows=ml_outputs.emotion_by_ad_rows,
    )
    top_emotions = sorted(
        [{"emotion": k, "count": v} for k, v in ml_outputs.emotion_counts.items()],
        key=lambda r: -r["count"],
    )
    visual_files = _time_stage("visualization", lambda: run_visuals(kpi_rows, visual_dir))
    yearly_summary = _time_stage(
        "summary_generation",
        lambda: run_summary(
            event,
            year,
            kpi_rows,
            f"{summary_dir}/yearly_summary.md",
            top_hashtags=hashtag_rows,
            top_mentions=mention_rows,
            top_emotions=top_emotions,
        ),
    )

    findings = [f"{r['kpi_id']}: {r['value']}" for r in kpi_rows]
    narratives = _time_stage(
        "narratives_generation",
        lambda: run_narratives(
            event,
            year,
            findings=findings,
            methodology=["Config-driven single-pass pipeline"],
            limitations=["MVP enrichment is minimal"],
            out_dir=summary_dir,
        ),
    )
    traceability_file = _time_stage(
        "traceability",
        lambda: build_traceability(
            kpi_rows,
            claims=["Engagement trends are derived from KPI outputs."],
            output_path=f"{summary_dir}/traceability.json",
        ),
    )
    infographic_export = _time_stage(
        "infographic_export",
        lambda: export_infographic_assets(visual_files, f"{visual_dir}/infographic_assets.json"),
    )

    quality = summarize_quality(total_cleaning_report)
    write_json_log(log_path, "INFO", "quality_summary", **quality)
    total_elapsed = time.perf_counter() - run_started_at
    timing_path = f"{manifest_dir}/timing_profile.json"
    timing_payload = {
        "year": year,
        "event_name": event,
        "total_seconds": round(total_elapsed, 3),
        "stage_seconds": {k: round(v, 3) for k, v in sorted(stage_seconds.items(), key=lambda kv: -kv[1])},
    }
    write_json(timing_path, timing_payload)

    artifacts = [
        {"artifact_id": "kpis", "artifact_type": "kpi", "year": year, "file_path": kpi_file},
        {"artifact_id": "hashtag_frequencies", "artifact_type": "dataset", "year": year, "file_path": hashtag_freq_file},
        {"artifact_id": "mention_frequencies", "artifact_type": "dataset", "year": year, "file_path": mention_freq_file},
        {"artifact_id": "lexicon_emotion_by_ad", "artifact_type": "dataset", "year": year, "file_path": lex_emotion_by_ad_file},
        {"artifact_id": "lexicon_emotion_examples", "artifact_type": "dataset", "year": year, "file_path": lex_emotion_examples_file},
        {"artifact_id": "lexicon_similar_hashtags", "artifact_type": "dataset", "year": year, "file_path": lex_similar_hashtags_file},
        {"artifact_id": "lexicon_emotion_overview", "artifact_type": "dataset", "year": year, "file_path": lex_emotion_overview_file},
        {"artifact_id": "ml_emotion_by_ad", "artifact_type": "dataset", "year": year, "file_path": ml_emotion_by_ad_file},
        {"artifact_id": "ml_emotion_examples", "artifact_type": "dataset", "year": year, "file_path": ml_emotion_examples_file},
        {"artifact_id": "ml_similar_hashtags", "artifact_type": "dataset", "year": year, "file_path": ml_similar_hashtags_file},
        {"artifact_id": "ml_emotion_overview", "artifact_type": "dataset", "year": year, "file_path": ml_emotion_overview_file},
        {"artifact_id": "brand_popularity", "artifact_type": "dataset", "year": year, "file_path": brand_popularity_file},
        {"artifact_id": "roi_join_ready", "artifact_type": "dataset", "year": year, "file_path": roi_join_ready_file},
        {"artifact_id": "timing_profile", "artifact_type": "dataset", "year": year, "file_path": timing_path},
        {"artifact_id": "visuals", "artifact_type": "visualization", "year": year, "file_path": visual_files[0]},
        {"artifact_id": "summary", "artifact_type": "summary", "year": year, "file_path": yearly_summary},
        {"artifact_id": "narrative", "artifact_type": "summary", "year": year, "file_path": narratives[0]},
        {"artifact_id": "traceability", "artifact_type": "summary", "year": year, "file_path": traceability_file},
        {"artifact_id": "infographic", "artifact_type": "visualization", "year": year, "file_path": infographic_export},
    ]
    artifact_index_path = f"{manifest_dir}/artifact_index.json"
    write_artifact_index(artifact_index_path, artifacts)

    kpi_defs = load_kpi_definitions("config/kpi_definitions.yaml")
    manifest_payload = {
        "run_id": run_id,
        "event_name": event,
        "year": year,
        "status": "succeeded",
        "config_path": config_path,
        "config_hash": _config_hash(config_path),
        "kpi_definition_version": kpi_defs.get("version", "unknown"),
        "quality_summary": quality,
        "artifact_index": artifact_index_path,
    }
    manifest_path = f"{manifest_dir}/run_manifest.json"
    write_manifest(manifest_path, manifest_payload)
    print(
        f"[run] done year={year} chunks={chunk_count} raw_rows={total_raw_rows} "
        f"accepted={quality['accepted_records']} rejected={quality['rejected_records']} "
        f"hashtags={len(hashtag_rows)} mentions={len(mention_rows)} "
        f"lexicon_emotion_ads={len(lex_outputs.emotion_by_ad_rows)} "
        f"ml_emotion_ads={len(ml_outputs.emotion_by_ad_rows)} "
        f"brands={len(brand_rows)} "
        f"ml_mode={ml_outputs.model_mode} total_seconds={total_elapsed:.2f} manifest={manifest_path}"
    )
    print(f"[run] timing profile written: {timing_path}")
    top_stages = sorted(stage_seconds.items(), key=lambda kv: -kv[1])[:5]
    for name, seconds in top_stages:
        print(f"[profile] {name}: {seconds:.2f}s")

    return {"run_id": run_id, "manifest_path": manifest_path, "artifact_index": artifact_index_path}


def main() -> None:
    args = parse_args()
    years: list[int]
    if args.years:
        years = [int(y.strip()) for y in args.years.split(",") if y.strip()]
    elif args.year:
        years = [args.year]
    else:
        raise SystemExit("Provide --year or --years")

    run_summaries = []
    for year in years:
        run_summaries.append(run_year(args.event, year, args.config))

    if len(years) > 1:
        all_rows = []
        for item in run_summaries:
            kpi_file = Path(item["manifest_path"]).parent.parent / "kpis" / "kpis.json"
            payload = json.loads(kpi_file.read_text(encoding="utf-8"))
            all_rows.extend(payload.get("kpis", []))
        yoy = build_year_over_year(all_rows)
        out = Path(f"outputs/{args.event}/year_over_year.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(yoy, indent=2), encoding="utf-8")
        print(f"[run] wrote year-over-year file: {out}")


if __name__ == "__main__":
    main()
