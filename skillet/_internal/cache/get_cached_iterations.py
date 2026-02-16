"""Load cached iteration results."""

from datetime import timedelta
from pathlib import Path

from cachetta import Cachetta, read_cache

_iter_cache = Cachetta(
    path=lambda cache_dir, iteration: cache_dir / f"iter-{iteration}.cache",
    duration=timedelta(days=36500),
)


def get_cached_iterations(cache_dir: Path) -> list[dict]:
    """Load all cached iteration results from a directory."""
    if not cache_dir.exists():
        return []

    results = []
    for f in sorted(cache_dir.glob("iter-*.cache")):
        iteration = int(f.stem.split("-")[1])
        with read_cache(_iter_cache, cache_dir, iteration) as data:
            if data is not None:
                results.append(data)

    return results
