import csv
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from src.agents.sentiment.agents.emotion import run_emotion
from src.agents.sentiment.agents.normalizer import run_normalizer
from src.agents.sentiment.agents.polarity import run_polarity
from src.agents.sentiment.agents.sarcasm import run_sarcasm
from src.agents.sentiment.config import AgentModelConfig, RuntimeConfig, get_openrouter_api_key
from src.agents.sentiment.llm import OpenRouterJsonClient
from src.agents.sentiment.schemas.final_record import SentimentRecord
from src.agents.sentiment.supervisor.supervisor import adjudicate_final
from src.agents.sentiment.writer import write_records, write_summary
from src.pipeline.stage_runtime import make_manifest


def _build_clients(model_cfg: AgentModelConfig, runtime_cfg: RuntimeConfig) -> dict[str, OpenRouterJsonClient] | None:
    if runtime_cfg.dry_run:
        return None
    api_key = get_openrouter_api_key(required=True)
    return {
        "normalizer": OpenRouterJsonClient(
            model=model_cfg.normalizer_model,
            api_key=api_key,
            request_delay_seconds=runtime_cfg.request_delay_seconds,
            max_rate_limit_retries=runtime_cfg.max_rate_limit_retries,
            initial_backoff_seconds=runtime_cfg.initial_backoff_seconds,
        ),
        "polarity": OpenRouterJsonClient(
            model=model_cfg.polarity_model,
            api_key=api_key,
            request_delay_seconds=runtime_cfg.request_delay_seconds,
            max_rate_limit_retries=runtime_cfg.max_rate_limit_retries,
            initial_backoff_seconds=runtime_cfg.initial_backoff_seconds,
        ),
        "emotion": OpenRouterJsonClient(
            model=model_cfg.emotion_model,
            api_key=api_key,
            request_delay_seconds=runtime_cfg.request_delay_seconds,
            max_rate_limit_retries=runtime_cfg.max_rate_limit_retries,
            initial_backoff_seconds=runtime_cfg.initial_backoff_seconds,
        ),
        "sarcasm": OpenRouterJsonClient(
            model=model_cfg.sarcasm_model,
            api_key=api_key,
            request_delay_seconds=runtime_cfg.request_delay_seconds,
            max_rate_limit_retries=runtime_cfg.max_rate_limit_retries,
            initial_backoff_seconds=runtime_cfg.initial_backoff_seconds,
        ),
    }


def _row_tweet_id(row: dict[str, str]) -> str:
    return row.get("id") or row.get("tweet_id") or ""


def run_sentiment_for_config(
    *,
    year: str,
    cleaned_csv: Path,
    analytics_dir: Path,
    model_cfg: AgentModelConfig | None = None,
    runtime_cfg: RuntimeConfig | None = None,
) -> tuple[Path, Path, object]:
    model_cfg = model_cfg or AgentModelConfig()
    runtime_cfg = runtime_cfg or RuntimeConfig()
    clients = _build_clients(model_cfg, runtime_cfg)

    rows = []
    with cleaned_csv.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)

    records: list[dict] = []
    for row in sorted(rows, key=lambda r: (_row_tweet_id(r), r.get("created_at_utc", ""))):
        tweet_id = _row_tweet_id(row)
        text = row.get("text", "")

        normalizer = run_normalizer(text, llm_client=None if clients is None else clients["normalizer"])
        norm_text = normalizer.normalized_text

        with ThreadPoolExecutor(max_workers=3) as pool:
            f_polarity = pool.submit(run_polarity, norm_text, None if clients is None else clients["polarity"])
            f_emotion = pool.submit(run_emotion, norm_text, None if clients is None else clients["emotion"])
            f_sarcasm = pool.submit(run_sarcasm, norm_text, None if clients is None else clients["sarcasm"])
            polarity = f_polarity.result()
            emotion = f_emotion.result()
            sarcasm = f_sarcasm.result()

        final, flags = adjudicate_final(polarity=polarity, emotion=emotion, sarcasm=sarcasm)
        record = SentimentRecord(
            tweet_id=tweet_id,
            year=int(year),
            final=final,
            agents={
                "polarity": polarity,
                "emotion": emotion,
                "sarcasm": sarcasm,
                "normalizer": normalizer,
            },
            flags=flags,
        ).model_dump()
        records.append(record)

    records_path = analytics_dir / "sentiment_agentic.jsonl"
    summary_path = analytics_dir / "sentiment_agentic_summary.json"
    write_records(records_path, records)
    write_summary(summary_path, int(year), records)
    manifest = make_manifest([cleaned_csv], [records_path, summary_path], len(rows), len(records))
    return records_path, summary_path, manifest

