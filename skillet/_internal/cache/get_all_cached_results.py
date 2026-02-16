"""Get all cached results for a name + skill."""

from pathlib import Path

from skillet import config

from .get_cached_iterations import get_cached_iterations
from .hash_directory import hash_directory
from .normalize_cache_name import normalize_cache_name


def get_all_cached_results(name: str, skill_path: Path | None = None) -> dict[str, list[dict]]:
    """Get all cached results for a name + skill, keyed by eval source.

    Returns: {"001.yaml": [iter1, iter2, ...], "002.yaml": [...], ...}
    """
    cache_base = config.CACHE_DIR / normalize_cache_name(name)
    if not cache_base.exists():
        return {}

    results = {}

    # Find all eval directories
    for eval_dir in cache_base.iterdir():
        if not eval_dir.is_dir():
            continue

        # Extract eval source from key (e.g., "001-abc123" -> "001.yaml")
        eval_key = eval_dir.name
        eval_source = eval_key.rsplit("-", 1)[0] + ".yaml"

        # Get the right subdirectory (baseline or skills/<hash>)
        if skill_path is None:
            iter_dir = eval_dir / "baseline"
        else:
            skill_hash = hash_directory(skill_path)
            iter_dir = eval_dir / "skills" / skill_hash

        iterations = get_cached_iterations(iter_dir)
        if iterations:
            results[eval_source] = iterations

    return results
