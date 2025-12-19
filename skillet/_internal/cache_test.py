"""Tests for cache module."""

import tempfile
from pathlib import Path

import pytest

from skillet._internal.cache import (
    gap_cache_key,
    get_cache_dir,
    get_cached_iterations,
    hash_content,
    hash_directory,
    hash_file,
    normalize_cache_name,
    save_iteration,
)


def describe_hash_content():
    """Tests for hash_content function."""

    def it_returns_12_char_hash():
        result = hash_content("test content")
        assert len(result) == 12

    def it_is_deterministic():
        assert hash_content("hello") == hash_content("hello")

    def it_differs_for_different_content():
        assert hash_content("hello") != hash_content("world")


def describe_hash_file():
    """Tests for hash_file function."""

    def it_hashes_file_contents():
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.txt"
            path.write_text("test content")
            result = hash_file(path)
            assert len(result) == 12

    def it_is_deterministic():
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.txt"
            path.write_text("test content")
            assert hash_file(path) == hash_file(path)


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

    def it_falls_back_to_hash_file_for_non_directory():
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "skill.md"
            path.write_text("# Skill content")
            result = hash_directory(path)
            assert len(result) == 12

    def it_includes_multiple_files():
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir)
            (skill_dir / "SKILL.md").write_text("# Main skill")
            (skill_dir / "extra.md").write_text("# Extra content")

            hash1 = hash_directory(skill_dir)

            # Changing any file should change the hash
            (skill_dir / "extra.md").write_text("# Modified extra")
            hash2 = hash_directory(skill_dir)

            assert hash1 != hash2


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

    def it_strips_yaml_extension():
        key = gap_cache_key("myeval.yaml", "content")
        assert "myeval-" in key
        assert ".yaml" not in key


def describe_normalize_cache_name():
    """Tests for normalize_cache_name function."""

    def it_returns_name_for_nonexistent_path():
        result = normalize_cache_name("nonexistent-path-12345")
        assert result == "nonexistent-path-12345"

    def it_returns_directory_name_for_existing_path():
        with tempfile.TemporaryDirectory() as tmpdir:
            result = normalize_cache_name(tmpdir)
            assert result == Path(tmpdir).name


def describe_get_cache_dir():
    """Tests for get_cache_dir function."""

    def it_returns_baseline_when_no_skill():
        result = get_cache_dir("myevals", "gap-abc123", skill_path=None)
        assert "baseline" in str(result)
        assert "myevals" in str(result)
        assert "gap-abc123" in str(result)

    def it_returns_skill_hash_path_when_skill_provided():
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir)
            (skill_dir / "SKILL.md").write_text("# Test")

            result = get_cache_dir("myevals", "gap-abc123", skill_path=skill_dir)
            assert "skills" in str(result)
            assert "myevals" in str(result)


def describe_get_cached_iterations():
    """Tests for get_cached_iterations function."""

    def it_returns_empty_list_for_nonexistent_dir():
        result = get_cached_iterations(Path("/nonexistent/path/12345"))
        assert result == []

    def it_loads_iteration_files():
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            (cache_dir / "iter-0.yaml").write_text("passed: true\nreasoning: good")
            (cache_dir / "iter-1.yaml").write_text("passed: false\nreasoning: bad")

            result = get_cached_iterations(cache_dir)
            assert len(result) == 2
            assert result[0]["passed"] is True
            assert result[1]["passed"] is False

    def it_returns_sorted_results():
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            (cache_dir / "iter-2.yaml").write_text("index: 2")
            (cache_dir / "iter-0.yaml").write_text("index: 0")
            (cache_dir / "iter-1.yaml").write_text("index: 1")

            result = get_cached_iterations(cache_dir)
            assert result[0]["index"] == 0
            assert result[1]["index"] == 1
            assert result[2]["index"] == 2


def describe_save_iteration():
    """Tests for save_iteration function."""

    def it_creates_directory_if_needed():
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "new" / "nested" / "dir"
            save_iteration(cache_dir, 0, {"passed": True})

            assert cache_dir.exists()
            assert (cache_dir / "iter-0.yaml").exists()

    def it_saves_yaml_content():
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            save_iteration(cache_dir, 5, {"passed": True, "reasoning": "looks good"})

            content = (cache_dir / "iter-5.yaml").read_text()
            assert "passed: true" in content
            assert "reasoning: looks good" in content
