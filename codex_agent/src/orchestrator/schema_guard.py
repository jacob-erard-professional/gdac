def ensure_kpi_schema(rows: list[dict]) -> None:
    required = {"run_id", "event_name", "year", "kpi_id", "value"}
    for row in rows:
        missing = required - set(row.keys())
        if missing:
            raise ValueError(f"Missing KPI fields: {sorted(missing)}")
