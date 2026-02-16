"""Get cache directory paths."""

from pathlib import Path

from skillet import config

from .hash_directory import hash_directory
from .normalize_cache_name import normalize_cache_name


def get_cache_dir(name: str, eval_key: str, skill_path: Path | None = None) -> Path:
    """Get cache directory for a specific eval + skill combo.

    Structure: ~/.skillet/cache/<name>/<eval-key>/baseline/
           or: ~/.skillet/cache/<name>/<eval-key>/skills/<skill-hash>/
    """
    base = config.CACHE_DIR / normalize_cache_name(name) / eval_key

    if skill_path is None:
        return base / "baseline"
    else:
        skill_hash = hash_directory(skill_path)
        return base / "skills" / skill_hash
