"""Tests for cache module."""

import tempfile
from pathlib import Path

import pytest

from skillet._internal.cache import gap_cache_key, hash_directory


def describe_gap_cache_key():
    """Tests for gap_cache_key function."""

    def it_is_deterministic():
        key1 = gap_cache_key("test.yaml", "prompt: hello\nexpected: world")
        key2 = gap_cache_key("test.yaml", "prompt: hello\nexpected: world")
        assert key1 == key2

    @pytest.mark.parametrize(
        "content1,content2",
        [
            ("prompt: hello", "prompt: goodbye"),
            ("expected: foo", "expected: bar"),
            ("a: 1", "a: 2"),
        ],
    )
    def it_differs_on_content(content1, content2):
        key1 = gap_cache_key("test.yaml", content1)
        key2 = gap_cache_key("test.yaml", content2)
        assert key1 != key2

    @pytest.mark.parametrize(
        "source1,source2",
        [
            ("test1.yaml", "test2.yaml"),
            ("a.yaml", "b.yaml"),
        ],
    )
    def it_differs_on_source(source1, source2):
        key1 = gap_cache_key(source1, "prompt: hello")
        key2 = gap_cache_key(source2, "prompt: hello")
        assert key1 != key2


def describe_hash_directory():
    """Tests for hash_directory function."""

    def it_is_deterministic():
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir)
            (skill_dir / "SKILL.md").write_text("# Test Skill\n")

            hash1 = hash_directory(skill_dir)
            hash2 = hash_directory(skill_dir)
            assert hash1 == hash2

    def it_changes_on_content_change():
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir)
            (skill_dir / "SKILL.md").write_text("# Test Skill v1\n")
            hash1 = hash_directory(skill_dir)

            (skill_dir / "SKILL.md").write_text("# Test Skill v2\n")
            hash2 = hash_directory(skill_dir)

            assert hash1 != hash2
