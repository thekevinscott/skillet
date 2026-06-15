"""Build the cachetta cache for a single eval run's iteration results."""

from datetime import timedelta
from pathlib import Path

from cachetta import Cachetta

from skillet.agent import Agent

from .eval_cache_key import eval_cache_key
from .hash_directory import hash_directory
from .normalize_cache_name import normalize_cache_name

# Eval results do not expire on their own: a changed eval or skill produces a
# new cache key, so a stale key is simply never read again. Until cachetta
# supports an explicit "never expires" duration, use a very large window.
_CACHE_DURATION = timedelta(days=36500)

# run_single_eval tags infra failures (setup-script failure, exceptions) with
# this key in their result payload; the condition hook below keeps those out of
# the cache so only genuine eval outcomes are persisted.
INFRA_FAILURE_KEY = "infra_failure"


def _is_cacheable(payload: dict) -> bool:
    """Cache real eval outcomes; skip infra failures (setup failure, exceptions)."""
    return not payload.get(INFRA_FAILURE_KEY, False)


def build_iteration_cache(
    cache_root: Path, name: str, skill_path: Path | None, agent: Agent
) -> Cachetta:
    """Return a cache for one eval run's iteration results.

    The cache is keyed by eval (filename + content hash), agent, and iteration
    under a per-run directory, mirroring the previous on-disk layout::

        <cache_root>/<name>/<eval-key>/<agent>/baseline/iter-<n>.cache
        <cache_root>/<name>/<eval-key>/<agent>/skills/<skill-hash>/iter-<n>.cache

    The agent is part of the key so ``claude`` and ``codex`` runs never collide.
    ``name``, ``skill_path``, and ``agent`` are fixed for a single run, so they
    (and the skill hash) are resolved once here; only the eval key and iteration
    vary per task and are read from the wrapped function's ``task`` argument.
    """
    name_dir = cache_root / normalize_cache_name(name)
    if skill_path is None:
        skill_subdir = Path("baseline")
    else:
        skill_subdir = Path("skills") / hash_directory(skill_path)

    def path(task: dict, *_: object) -> Path:
        eval_key = eval_cache_key(task["eval_source"], task["eval_content"])
        return name_dir / eval_key / agent.value / skill_subdir / f"iter-{task['iteration']}.cache"

    return Cachetta(path=path, condition=_is_cacheable, duration=_CACHE_DURATION)
