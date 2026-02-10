from __future__ import annotations

import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterable, List, TypeVar

from concurrent.futures import ThreadPoolExecutor

T = TypeVar("T")


def _lock_path(target: Path) -> Path:
    return target.with_suffix(target.suffix + ".lock")


@contextmanager
def file_lock(target: Path, timeout_seconds: int = 30):
    lock_path = _lock_path(target)
    start = time.time()
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            if time.time() - start > timeout_seconds:
                raise TimeoutError(f"Timeout acquiring lock: {lock_path}")
            time.sleep(0.1)
    try:
        yield
    finally:
        if lock_path.exists():
            lock_path.unlink()


def run_in_parallel(tasks: Iterable[Callable[[], T]], max_workers: int = 4) -> List[T]:
    results: List[T] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(task) for task in tasks]
        for future in futures:
            results.append(future.result())
    return results
