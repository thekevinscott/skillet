"""Tests for compare/get_cached_results_for_eval module."""

import tempfile
from pathlib import Path

import pytest

import skillet.config
from skillet.compare.get_cached_results_for_eval import get_cached_results_for_eval


def describe_get_cached_results_for_eval():
    @pytest.fixture(autouse=True)
    def mock_cache_dir(monkeypatch):
        monkeypatch.setattr(skillet.config, "CACHE_DIR", Path("/tmp/fake-cache"))

    def it_returns_empty_for_nonexistent_cache():
        eval_item = {"_source": "test.yaml", "_content": "prompt: test\nexpected: result"}
        result = get_cached_results_for_eval("nonexistent-name-12345", eval_item, None)
        assert result == []

    def it_uses_baseline_path_when_no_skill():
        eval_item = {"_source": "test.yaml", "_content": "prompt: test"}
        result = get_cached_results_for_eval("myevals", eval_item, None)
        assert result == []

    def it_uses_skill_hash_path_when_skill_provided():
        eval_item = {"_source": "test.yaml", "_content": "prompt: test"}
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir)
            (skill_path / "SKILL.md").write_text("# Test skill")

            result = get_cached_results_for_eval("myevals", eval_item, skill_path)
            assert result == []
