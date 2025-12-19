"""Tests for compare/get_cached_results_for_gap module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from skillet.compare.get_cached_results_for_gap import get_cached_results_for_gap


def describe_get_cached_results_for_gap():
    """Tests for get_cached_results_for_gap function."""

    def it_returns_empty_for_nonexistent_cache():
        gap = {"_source": "test.yaml", "_content": "prompt: test\nexpected: result"}
        result = get_cached_results_for_gap("nonexistent-name-12345", gap, None)
        assert result == []

    def it_uses_baseline_path_when_no_skill():
        gap = {"_source": "test.yaml", "_content": "prompt: test"}
        with patch(
            "skillet.compare.get_cached_results_for_gap.CACHE_DIR", Path("/tmp/fake-cache")
        ):
            result = get_cached_results_for_gap("myevals", gap, None)
            assert result == []

    def it_uses_skill_hash_path_when_skill_provided():
        gap = {"_source": "test.yaml", "_content": "prompt: test"}
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir)
            (skill_path / "SKILL.md").write_text("# Test skill")

            with patch(
                "skillet.compare.get_cached_results_for_gap.CACHE_DIR", Path("/tmp/fake-cache")
            ):
                result = get_cached_results_for_gap("myevals", gap, skill_path)
                assert result == []
