"""Get cache directory paths."""

from pathlib import Path

from skillet.config import SKILLET_DIR

from .hash_directory import hash_directory
from .normalize_cache_name import normalize_cache_name

CACHE_DIR = SKILLET_DIR / "cache"


def get_cache_dir(name: str, eval_key: str, skill_path: Path | None = None) -> Path:
    """Get cache directory for a specific eval + skill combo.

    Structure: ~/.skillet/cache/<name>/<eval-key>/baseline/
           or: ~/.skillet/cache/<name>/<eval-key>/skills/<skill-hash>/
    """
    base = CACHE_DIR / normalize_cache_name(name) / eval_key

    if skill_path is None:
        return base / "baseline"
    else:
        skill_hash = hash_directory(skill_path)
        return base / "skills" / skill_hash
