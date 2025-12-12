"""Tests for cache module."""

import tempfile
from pathlib import Path

from skillet.cache import gap_cache_key, hash_directory


def test_gap_cache_key_deterministic():
    """Gap cache key is deterministic for same input."""
    key1 = gap_cache_key("test.yaml", "prompt: hello\nexpected: world")
    key2 = gap_cache_key("test.yaml", "prompt: hello\nexpected: world")
    assert key1 == key2


def test_gap_cache_key_differs_on_content():
    """Gap cache key changes when content changes."""
    key1 = gap_cache_key("test.yaml", "prompt: hello\nexpected: world")
    key2 = gap_cache_key("test.yaml", "prompt: goodbye\nexpected: world")
    assert key1 != key2


def test_gap_cache_key_differs_on_source():
    """Gap cache key changes when source file changes."""
    key1 = gap_cache_key("test1.yaml", "prompt: hello")
    key2 = gap_cache_key("test2.yaml", "prompt: hello")
    assert key1 != key2


def test_hash_directory_deterministic():
    """Directory hash is deterministic for same content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir)
        (skill_dir / "SKILL.md").write_text("# Test Skill\n")

        hash1 = hash_directory(skill_dir)
        hash2 = hash_directory(skill_dir)
        assert hash1 == hash2


def test_hash_directory_changes_on_content():
    """Directory hash changes when file content changes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir)
        (skill_dir / "SKILL.md").write_text("# Test Skill v1\n")
        hash1 = hash_directory(skill_dir)

        (skill_dir / "SKILL.md").write_text("# Test Skill v2\n")
        hash2 = hash_directory(skill_dir)

        assert hash1 != hash2
