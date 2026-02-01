"""Shared caching utilities for classification results."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CacheManager:
    """Manages caching of classification results by content hash."""

    cache_dir: Path
    skip_cache: bool = False

    def get_cache_key(self, content: str) -> str:
        """Generate cache key from content hash (SHA256 truncated to 16 chars)."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def get(self, content: str) -> dict | None:
        """Get cached result for content, or None if not cached."""
        if self.skip_cache:
            return None
        cache_file = self.cache_dir / f"{self.get_cache_key(content)}.json"
        if cache_file.exists():
            try:
                return json.loads(cache_file.read_text())
            except json.JSONDecodeError:
                return None
        return None

    def set(self, content: str, result: dict):
        """Cache a result for the given content."""
        cache_file = self.cache_dir / f"{self.get_cache_key(content)}.json"
        cache_file.write_text(json.dumps(result))
