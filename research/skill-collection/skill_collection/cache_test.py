"""Unit tests for cache module."""

import pytest

from .cache import CacheManager


def describe_CacheManager():
    @pytest.fixture
    def cache(tmp_path):
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir(parents=True)
        return CacheManager(cache_dir=cache_dir)

    def it_generates_consistent_cache_keys(cache):
        content = "test content"
        key1 = cache.get_cache_key(content)
        key2 = cache.get_cache_key(content)
        assert key1 == key2
        assert len(key1) == 16  # SHA256 truncated to 16 chars

    def it_generates_different_keys_for_different_content(cache):
        key1 = cache.get_cache_key("content A")
        key2 = cache.get_cache_key("content B")
        assert key1 != key2

    def it_returns_none_for_uncached_content(cache):
        result = cache.get("new content")
        assert result is None

    def it_caches_and_retrieves_results(cache):
        content = "test content"
        expected = {"is_skill_file": True, "reason": "test"}
        cache.set(content, expected)
        result = cache.get(content)
        assert result == expected

    def it_respects_skip_cache_flag(tmp_path):
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir(parents=True)
        cache = CacheManager(cache_dir=cache_dir, skip_cache=True)
        cache.set("content", {"is_skill_file": True})
        result = cache.get("content")
        assert result is None

    def it_creates_cache_dir_if_missing(tmp_path):
        cache_dir = tmp_path / "new_cache"
        cache = CacheManager(cache_dir=cache_dir)
        cache.set("content", {"key": "value"})
        assert cache_dir.exists()
        assert cache.get("content") == {"key": "value"}
