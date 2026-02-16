"""Save iteration results to cache."""

from pathlib import Path

from cachetta import write_cache

from .get_cached_iterations import _iter_cache


def save_iteration(cache_dir: Path, iteration: int, result: dict):
    """Save a single iteration result to cache."""
    write_cache(_iter_cache, result, cache_dir, iteration)
