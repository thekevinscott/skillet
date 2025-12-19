"""Get cached results for a specific eval."""

from pathlib import Path

from skillet._internal.cache import (
    CACHE_DIR,
    eval_cache_key,
    get_cached_iterations,
    hash_directory,
)


def get_cached_results_for_eval(name: str, eval_item: dict, skill_path: Path | None) -> list[dict]:
    """Get cached iteration results for a specific eval."""
    eval_key = eval_cache_key(eval_item["_source"], eval_item["_content"])
    cache_base = CACHE_DIR / name / eval_key

    if skill_path is None:
        cache_dir = cache_base / "baseline"
    else:
        skill_hash = hash_directory(skill_path)
        cache_dir = cache_base / "skills" / skill_hash

    return get_cached_iterations(cache_dir)
