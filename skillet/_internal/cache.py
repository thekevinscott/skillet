"""Caching for eval results."""

import hashlib
from pathlib import Path

import yaml

from skillet._internal.lock import cache_lock  # noqa: F401
from skillet.config import SKILLET_DIR

CACHE_DIR = SKILLET_DIR / "cache"


def hash_content(content: str) -> str:
    """Return short md5 hash of content."""
    return hashlib.md5(content.encode()).hexdigest()[:12]


def hash_file(path: Path) -> str:
    """Return short md5 hash of file contents."""
    return hash_content(path.read_text())


def hash_directory(path: Path) -> str:
    """Return hash of all files in directory (sorted, concatenated)."""
    if not path.is_dir():
        return hash_file(path)

    contents = []
    for f in sorted(path.rglob("*")):
        if f.is_file():
            contents.append(f"{f.relative_to(path)}:{f.read_text()}")

    return hash_content("\n".join(contents))


def eval_cache_key(eval_source: str, eval_content: str) -> str:
    """Return cache key for an eval: <filename>-<content-hash>."""
    content_hash = hash_content(eval_content)
    # Remove .yaml extension for cleaner key
    name = eval_source.replace(".yaml", "")
    return f"{name}-{content_hash}"


def normalize_cache_name(name: str) -> str:
    """Normalize name to cache key: if path exists, use directory name."""
    name_path = Path(name)
    return name_path.resolve().name if name_path.exists() else name


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


def get_cached_iterations(cache_dir: Path) -> list[dict]:
    """Load all cached iteration results from a directory."""
    if not cache_dir.exists():
        return []

    results = []
    for f in sorted(cache_dir.glob("iter-*.yaml")):
        with f.open() as fp:
            results.append(yaml.safe_load(fp))

    return results


def save_iteration(cache_dir: Path, iteration: int, result: dict):
    """Save a single iteration result to cache."""
    cache_dir.mkdir(parents=True, exist_ok=True)

    cache_file = cache_dir / f"iter-{iteration}.yaml"
    with cache_file.open("w") as f:
        yaml.dump(result, f, default_flow_style=False)


def get_all_cached_results(name: str, skill_path: Path | None = None) -> dict[str, list[dict]]:
    """Get all cached results for a name + skill, keyed by eval source.

    Returns: {"001.yaml": [iter1, iter2, ...], "002.yaml": [...], ...}
    """
    cache_base = CACHE_DIR / normalize_cache_name(name)
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
