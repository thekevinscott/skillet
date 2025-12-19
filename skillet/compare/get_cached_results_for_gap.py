"""Get cached results for a specific gap."""

from pathlib import Path

from skillet._internal.cache import (
    CACHE_DIR,
    gap_cache_key,
    get_cached_iterations,
    hash_directory,
)


def get_cached_results_for_gap(name: str, gap: dict, skill_path: Path | None) -> list[dict]:
    """Get cached iteration results for a specific gap."""
    gap_key = gap_cache_key(gap["_source"], gap["_content"])
    cache_base = CACHE_DIR / name / gap_key

    if skill_path is None:
        cache_dir = cache_base / "baseline"
    else:
        skill_hash = hash_directory(skill_path)
        cache_dir = cache_base / "skills" / skill_hash

    return get_cached_iterations(cache_dir)
