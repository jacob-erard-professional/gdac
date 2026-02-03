from pathlib import Path


def discover_years(raw_root: Path):
    if not raw_root.exists():
        return []
    years = [p.name for p in raw_root.iterdir() if p.is_dir() and p.name.isdigit() and len(p.name) == 4]
    return sorted(years)
