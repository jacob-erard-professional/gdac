from pathlib import Path


def ensure_not_raw_output(path: Path) -> None:
    norm = str(path).replace('\\', '/')
    if '/data/raw/' in norm or norm.endswith('/data/raw'):
        raise ValueError('writes to data/raw are not allowed')
