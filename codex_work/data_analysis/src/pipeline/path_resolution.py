from pathlib import Path
from .config import YearConfig, validate_year


def resolve_year_config(base_dir: Path, year: str | None = None, data_dir: Path | None = None) -> YearConfig:
    if bool(year) == bool(data_dir):
        raise ValueError("Provide exactly one of year or data_dir")
    if data_dir:
        raw_dir = Path(data_dir)
        if not raw_dir.is_absolute():
            raw_dir = (base_dir / raw_dir).resolve()
        y = raw_dir.name
        validate_year(y)
        return YearConfig(
            year=y,
            raw_dir=raw_dir,
            processed_dir=base_dir / "data" / "processed" / y,
            enriched_dir=base_dir / "data" / "enriched" / y,
            analytics_dir=base_dir / "outputs" / "analytics" / y,
        )
    assert year is not None
    validate_year(year)
    return YearConfig(
        year=year,
        raw_dir=base_dir / "data" / "raw" / year,
        processed_dir=base_dir / "data" / "processed" / year,
        enriched_dir=base_dir / "data" / "enriched" / year,
        analytics_dir=base_dir / "outputs" / "analytics" / year,
    )
