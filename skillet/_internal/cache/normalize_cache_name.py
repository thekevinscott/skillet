"""Normalize cache names."""

from pathlib import Path


def normalize_cache_name(name: str) -> str:
    """Normalize name to cache key: if path exists, use directory name."""
    name_path = Path(name)
    return name_path.resolve().name if name_path.exists() else name
