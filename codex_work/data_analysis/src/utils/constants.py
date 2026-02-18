"""Shared utilities for constants."""

STAGES = ["ingest", "clean", "process", "analyze", "visualize", "export"]
DATA_DIRS = {
    "raw": "data/raw",
    "processed": "data/processed",
    "enriched": "data/enriched",
    "analytics": "outputs/analytics",
}
METADATA_KEYS = ["input_files", "output_files", "record_counts", "started_at", "completed_at"]
