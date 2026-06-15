"""Get cache directory paths."""

from pathlib import Path

from skillet import config
from skillet.agent import Agent

from .hash_directory import hash_directory
from .normalize_cache_name import normalize_cache_name


def get_cache_dir(
    name: str, eval_key: str, skill_path: Path | None = None, *, agent: Agent
) -> Path:
    """Get cache directory for a specific eval + agent + skill combo.

    Structure: ~/.skillet/cache/<name>/<eval-key>/<agent>/baseline/
           or: ~/.skillet/cache/<name>/<eval-key>/<agent>/skills/<skill-hash>/

    The agent is part of the key so claude and codex runs never collide.
    """
    base = config.CACHE_DIR / normalize_cache_name(name) / eval_key / agent.value

    if skill_path is None:
        return base / "baseline"
    else:
        skill_hash = hash_directory(skill_path)
        return base / "skills" / skill_hash
