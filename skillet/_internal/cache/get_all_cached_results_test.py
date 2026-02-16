"""Tests for get_all_cached_results function."""

import tempfile
from pathlib import Path

import pytest

import skillet.config
from skillet._internal.cache import (
    get_all_cached_results,
    hash_directory,
    save_iteration,
)


def describe_get_all_cached_results():
    @pytest.fixture(autouse=True)
    def mock_cache_dir(monkeypatch):
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setattr(skillet.config, "CACHE_DIR", Path(tmpdir))
            yield Path(tmpdir)

    def it_returns_empty_dict_for_nonexistent_name():
        result = get_all_cached_results("nonexistent-name-12345")
        assert result == {}

    def it_returns_baseline_results_when_no_skill(mock_cache_dir):
        eval_dir = mock_cache_dir / "myevals" / "001-abc123" / "baseline"
        save_iteration(eval_dir, 0, {"passed": True})
        save_iteration(eval_dir, 1, {"passed": False})

        result = get_all_cached_results("myevals", skill_path=None)
        assert "001.yaml" in result
        assert len(result["001.yaml"]) == 2
        assert result["001.yaml"][0]["passed"] is True
        assert result["001.yaml"][1]["passed"] is False

    def it_returns_skill_results_when_skill_provided(mock_cache_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir)
            (skill_dir / "SKILL.md").write_text("# Test Skill")

            skill_hash = hash_directory(skill_dir)
            eval_dir = mock_cache_dir / "myevals" / "002-def456" / "skills" / skill_hash
            save_iteration(eval_dir, 0, {"passed": True})

            result = get_all_cached_results("myevals", skill_path=skill_dir)
            assert "002.yaml" in result
            assert len(result["002.yaml"]) == 1

    def it_returns_multiple_evals(mock_cache_dir):
        for eval_name in ["001-abc", "002-def", "003-ghi"]:
            eval_dir = mock_cache_dir / "myevals" / eval_name / "baseline"
            save_iteration(eval_dir, 0, {"passed": True})

        result = get_all_cached_results("myevals", skill_path=None)
        assert len(result) == 3
        assert "001.yaml" in result
        assert "002.yaml" in result
        assert "003.yaml" in result

    def it_ignores_files_in_cache_directory(mock_cache_dir):
        eval_dir = mock_cache_dir / "myevals" / "001-abc" / "baseline"
        save_iteration(eval_dir, 0, {"passed": True})

        # Create a file (not a directory) that should be ignored
        (mock_cache_dir / "myevals" / "somefile.txt").write_text("ignored")

        result = get_all_cached_results("myevals", skill_path=None)
        assert len(result) == 1
        assert "001.yaml" in result

    def it_skips_evals_with_no_iterations(mock_cache_dir):
        # Create eval dir with no iteration files
        empty_eval = mock_cache_dir / "myevals" / "001-abc" / "baseline"
        empty_eval.mkdir(parents=True)

        # Create eval dir with iterations
        full_eval = mock_cache_dir / "myevals" / "002-def" / "baseline"
        save_iteration(full_eval, 0, {"passed": True})

        result = get_all_cached_results("myevals", skill_path=None)
        assert len(result) == 1
        assert "002.yaml" in result
        assert "001.yaml" not in result
