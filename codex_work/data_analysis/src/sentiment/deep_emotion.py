import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from src.pipeline.stage_runtime import make_manifest

DEFAULT_MODEL_ID = "cardiffnlp/twitter-roberta-base-emotion-latest"
REQUIRED_EMOTIONS = set()

URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
HASHTAG_RE = re.compile(r"#(\w+)")



@dataclass(frozen=True)
class ModelBundle:
    model: Any
    tokenizer: Any
    model_id: str
    id2label: dict[int, str]
    canonical_id2label: dict[int, str]
    commit_hash: str | None


def preprocess_tweet_text(text: str) -> str:
    raw = "" if text is None else str(text)
    without_urls = URL_RE.sub("", raw)
    return " ".join(without_urls.split())


def extract_hashtags(text: str) -> list[str]:
    hashtags = {tag.lower() for tag in HASHTAG_RE.findall(text or "") if tag}
    return sorted(hashtags)


def _normalize_label_key(label: str) -> str:
    return str(label or "").strip().lower().replace("-", "_").replace(" ", "_")


def _normalize_target_label(label: str) -> str | None:
    normalized = _normalize_label_key(label)
    return normalized or None


def load_label_overrides(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Label map file must contain a JSON object of model_label -> target_label")

    overrides: dict[str, str] = {}
    for raw_model_label, raw_target_label in payload.items():
        normalized_key = _normalize_label_key(str(raw_model_label))
        normalized_target = _normalize_target_label(str(raw_target_label))
        if not normalized_target:
            raise ValueError(
                "Label map contains unsupported target label "
                f"'{raw_target_label}'. Provide a non-empty label."
            )
        overrides[normalized_key] = normalized_target
    return overrides


def validate_label_mapping(
    id2label: dict[Any, Any],
    *,
    label_overrides: dict[str, str] | None = None,
) -> dict[int, str]:
    if not id2label:
        raise ValueError("Model config is missing id2label mapping")

    overrides = label_overrides or {}
    canonical: dict[int, str] = {}

    for raw_idx, raw_label in id2label.items():
        idx = int(raw_idx)
        raw_label_str = str(raw_label)
        normalized_key = _normalize_label_key(raw_label_str)
        emotion = overrides.get(normalized_key) or _normalize_target_label(raw_label_str)
        if emotion is None:
            emotion = normalized_key
        canonical[idx] = emotion

    return canonical


def _require_dependencies() -> tuple[Any, Any, Any]:
    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "Missing ML dependencies. Install torch and transformers to run deep sentiment inference."
        ) from exc
    return torch, AutoModelForSequenceClassification, AutoTokenizer


def _resolve_device(torch: Any, device: str, logger: Callable[[str], None] | None = None) -> str:
    requested = str(device or "").strip().lower() or "cuda"
    if requested == "cuda":
        if torch.cuda.is_available():
            return "cuda"
        if logger:
            logger("[deep-sentiment] CUDA not available, falling back to CPU")
        return "cpu"
    return requested


def load_model_bundle(
    model_id: str,
    *,
    label_overrides: dict[str, str] | None = None,
) -> ModelBundle:
    _torch, auto_model_cls, auto_tokenizer_cls = _require_dependencies()
    tokenizer = auto_tokenizer_cls.from_pretrained(model_id, use_fast=False)
    model = auto_model_cls.from_pretrained(model_id)
    model.eval()

    raw_id2label = getattr(model.config, "id2label", None)
    canonical_id2label = validate_label_mapping(raw_id2label, label_overrides=label_overrides)
    id2label = {int(k): str(v) for k, v in raw_id2label.items()}

    commit_hash = getattr(model.config, "_commit_hash", None)
    if not commit_hash:
        init_kwargs = getattr(tokenizer, "init_kwargs", {})
        commit_hash = init_kwargs.get("_commit_hash")

    return ModelBundle(
        model=model,
        tokenizer=tokenizer,
        model_id=model_id,
        id2label=id2label,
        canonical_id2label=canonical_id2label,
        commit_hash=commit_hash,
    )


def load_input_rows(input_path: Path, *, target_year: int | None) -> tuple[list[dict[str, Any]], int]:
    suffix = input_path.suffix.lower()
    if suffix == ".csv":
        frame = pd.read_csv(input_path, dtype=str, keep_default_na=False)
    elif suffix == ".parquet":
        frame = pd.read_parquet(input_path)
    else:
        raise ValueError(f"Unsupported input format: {input_path}. Use .csv or .parquet")

    if frame.empty:
        return [], 0

    tweet_id_col = "tweet_id" if "tweet_id" in frame.columns else ("id" if "id" in frame.columns else None)
    if tweet_id_col is None:
        raise ValueError("Input is missing required tweet identifier column: tweet_id or id")
    if "text" not in frame.columns:
        raise ValueError("Input is missing required text column: text")

    if "year" in frame.columns:
        years = frame["year"]
    elif target_year is not None:
        years = pd.Series([target_year] * len(frame))
    else:
        raise ValueError("Input is missing year column and no --year was provided")

    created_at_col = "created_at_utc" if "created_at_utc" in frame.columns else "created_at"
    brand_col = (
        "brand"
        if "brand" in frame.columns
        else ("brand_ad_name" if "brand_ad_name" in frame.columns else ("brand_tag" if "brand_tag" in frame.columns else None))
    )

    normalized = pd.DataFrame(
        {
            "tweet_id": frame[tweet_id_col].astype(str),
            "text": frame["text"].astype(str).map(preprocess_tweet_text),
            "year": years,
            "created_at": frame[created_at_col].astype(str) if created_at_col in frame.columns else "",
            "pipeline_row_id": frame["pipeline_row_id"].astype(str) if "pipeline_row_id" in frame.columns else "",
            "username": frame["username"].astype(str) if "username" in frame.columns else "",
            "brand": frame[brand_col].astype(str) if brand_col else "",
        }
    )

    normalized["tweet_id"] = normalized["tweet_id"].map(lambda x: x.strip())
    normalized["year"] = pd.to_numeric(normalized["year"], errors="coerce")

    invalid_mask = normalized["tweet_id"].eq("") | normalized["text"].eq("") | normalized["year"].isna()
    invalid_count = int(invalid_mask.sum())

    valid = normalized.loc[~invalid_mask].copy()
    if valid.empty:
        return [], invalid_count

    valid["year"] = valid["year"].astype(int)
    valid["hashtags"] = valid["text"].map(extract_hashtags)
    valid["row_order"] = valid.index.astype(int)
    valid = valid.sort_values(by=["tweet_id", "created_at", "row_order"], kind="mergesort")

    rows = valid[["tweet_id", "text", "hashtags", "year", "pipeline_row_id", "username", "brand"]].to_dict(orient="records")
    return rows, invalid_count


def infer_deep_sentiment_batches(
    rows: list[dict[str, Any]],
    *,
    model_bundle: ModelBundle,
    batch_size: int,
    device: str,
    logger: Callable[[str], None] | None = None,
) -> list[dict[str, Any]]:
    if batch_size <= 0:
        raise ValueError("batch_size must be >= 1")
    if not rows:
        return []

    torch, _auto_model_cls, _auto_tokenizer_cls = _require_dependencies()
    device = _resolve_device(torch, device, logger)

    total = len(rows)
    out: list[dict[str, Any]] = []

    model = model_bundle.model
    if hasattr(model, "to"):
        model = model.to(device)
    for start in range(0, total, batch_size):
        batch = rows[start : start + batch_size]
        texts = [item["text"] for item in batch]

        tokenized = model_bundle.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors="pt",
        )
        tokenized = {
            k: (v.to(device) if hasattr(v, "to") else v) for k, v in tokenized.items()
        }

        with torch.no_grad():
            logits = model(**tokenized).logits
            probabilities = torch.softmax(logits, dim=-1)
            confidence_tensor, index_tensor = torch.max(probabilities, dim=-1)

        for row, confidence, index in zip(batch, confidence_tensor.tolist(), index_tensor.tolist()):
            label_idx = int(index)
            main_sentiment = model_bundle.canonical_id2label.get(label_idx)
            if not main_sentiment:
                raise ValueError(f"Unsupported predicted label index: {label_idx}")
            if float(confidence) < 0.65:
                main_sentiment = "neutral"

            out.append(
                {
                    "tweet_id": row["tweet_id"],
                    "hashtags": row["hashtags"],
                    "text": row["text"],
                    "year": int(row["year"]),
                    "pipeline_row_id": row.get("pipeline_row_id", ""),
                    "username": row.get("username", ""),
                    "brand": str(row.get("brand", "")).strip().lower(),
                    "main_sentiment": main_sentiment,
                    "confidence": round(float(confidence), 6),
                }
            )

        if logger:
            logger(f"Processed {min(start + len(batch), total)}/{total} tweets")

    return out


def write_deep_sentiment_output(
    *,
    output_path: Path,
    input_path: Path,
    model_bundle: ModelBundle,
    records: list[dict[str, Any]],
    invalid_rows: int,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "metadata": {
            "model_id": model_bundle.model_id,
            "model_commit_hash": model_bundle.commit_hash,
            "id2label": {str(k): v for k, v in sorted(model_bundle.id2label.items())},
            "canonical_id2label": {str(k): v for k, v in sorted(model_bundle.canonical_id2label.items())},
            "source_file": str(input_path),
            "invalid_rows_skipped": int(invalid_rows),
            "total_records": len(records),
            "taxonomy": sorted(set(model_bundle.canonical_id2label.values()) | {"neutral"}),
        },
        "records": records,
    }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def run_deep_sentiment(
    *,
    year: int,
    input_path: Path,
    output_root: Path,
    model_id: str = DEFAULT_MODEL_ID,
    batch_size: int = 64,
    dry_run: bool = False,
    label_map_file: Path | None = None,
    device: str = "cuda",
    logger: Callable[[str], None] | None = None,
):
    if logger:
        logger(f"[deep-sentiment] loading input rows from {input_path}")

    rows, invalid_rows = load_input_rows(input_path, target_year=year)
    if logger:
        logger(
            f"[deep-sentiment] loaded rows total={len(rows) + invalid_rows} "
            f"valid={len(rows)} invalid_skipped={invalid_rows}"
        )

    if dry_run:
        notes = [
            "dry_run=true",
            f"input_rows={len(rows) + invalid_rows}",
            f"valid_rows={len(rows)}",
            f"invalid_rows_skipped={invalid_rows}",
            f"model_id={model_id}",
        ]
        manifest = make_manifest([input_path], [], len(rows) + invalid_rows, 0, notes=notes)
        return None, manifest

    overrides = load_label_overrides(label_map_file)
    model_bundle = load_model_bundle(model_id, label_overrides=overrides)
    if logger:
        logger(f"[deep-sentiment] model loaded: {model_bundle.model_id}")

    records = infer_deep_sentiment_batches(
        rows,
        model_bundle=model_bundle,
        batch_size=batch_size,
        device=device,
        logger=logger,
    )

    output_path = output_root / "deep" / str(year) / "deep_sentiment.json"
    if logger:
        logger(f"[deep-sentiment] writing output to {output_path}")

    write_deep_sentiment_output(
        output_path=output_path,
        input_path=input_path,
        model_bundle=model_bundle,
        records=records,
        invalid_rows=invalid_rows,
    )

    notes = [
        f"model_id={model_bundle.model_id}",
        f"invalid_rows_skipped={invalid_rows}",
        f"label_map_file={label_map_file}" if label_map_file else "label_map_file=<default>",
    ]
    if model_bundle.commit_hash:
        notes.append(f"model_commit_hash={model_bundle.commit_hash}")

    manifest = make_manifest([input_path], [output_path], len(rows) + invalid_rows, len(records), notes=notes)
    if logger:
        logger("[deep-sentiment] complete")

    return output_path, manifest
