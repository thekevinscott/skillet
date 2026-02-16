"""Tests for get_all_cached_results function."""

import importlib
import tempfile
from pathlib import Path

from skillet._internal.cache import (
    get_all_cached_results,
    hash_directory,
    save_iteration,
)

# importlib needed to get the *module* (not the function re-exported by __init__)
_gacr_mod = importlib.import_module("skillet._internal.cache.get_all_cached_results")


def describe_get_all_cached_results():
    def it_returns_empty_dict_for_nonexistent_name():
        result = get_all_cached_results("nonexistent-name-12345")
        assert result == {}

    def it_returns_baseline_results_when_no_skill(monkeypatch):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_base = Path(tmpdir)
            monkeypatch.setattr(_gacr_mod, "CACHE_DIR", cache_base)

            eval_dir = cache_base / "myevals" / "001-abc123" / "baseline"
            save_iteration(eval_dir, 0, {"passed": True})
            save_iteration(eval_dir, 1, {"passed": False})

            result = get_all_cached_results("myevals", skill_path=None)
            assert "001.yaml" in result
            assert len(result["001.yaml"]) == 2
            assert result["001.yaml"][0]["passed"] is True
            assert result["001.yaml"][1]["passed"] is False

    def it_returns_skill_results_when_skill_provided(monkeypatch):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_base = Path(tmpdir)
            skill_dir = Path(tmpdir) / "skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("# Test Skill")

            monkeypatch.setattr(_gacr_mod, "CACHE_DIR", cache_base)

            skill_hash = hash_directory(skill_dir)
            eval_dir = cache_base / "myevals" / "002-def456" / "skills" / skill_hash
            save_iteration(eval_dir, 0, {"passed": True})

            result = get_all_cached_results("myevals", skill_path=skill_dir)
            assert "002.yaml" in result
            assert len(result["002.yaml"]) == 1

    def it_returns_multiple_evals(monkeypatch):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_base = Path(tmpdir)
            monkeypatch.setattr(_gacr_mod, "CACHE_DIR", cache_base)

            for eval_name in ["001-abc", "002-def", "003-ghi"]:
                eval_dir = cache_base / "myevals" / eval_name / "baseline"
                save_iteration(eval_dir, 0, {"passed": True})

            result = get_all_cached_results("myevals", skill_path=None)
            assert len(result) == 3
            assert "001.yaml" in result
            assert "002.yaml" in result
            assert "003.yaml" in result

    def it_ignores_files_in_cache_directory(monkeypatch):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_base = Path(tmpdir)
            monkeypatch.setattr(_gacr_mod, "CACHE_DIR", cache_base)

            eval_dir = cache_base / "myevals" / "001-abc" / "baseline"
            save_iteration(eval_dir, 0, {"passed": True})

            # Create a file (not a directory) that should be ignored
            (cache_base / "myevals" / "somefile.txt").write_text("ignored")

            result = get_all_cached_results("myevals", skill_path=None)
            assert len(result) == 1
            assert "001.yaml" in result

    def it_skips_evals_with_no_iterations(monkeypatch):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_base = Path(tmpdir)
            monkeypatch.setattr(_gacr_mod, "CACHE_DIR", cache_base)

            # Create eval dir with no iteration files
            empty_eval = cache_base / "myevals" / "001-abc" / "baseline"
            empty_eval.mkdir(parents=True)

            # Create eval dir with iterations
            full_eval = cache_base / "myevals" / "002-def" / "baseline"
            save_iteration(full_eval, 0, {"passed": True})

            result = get_all_cached_results("myevals", skill_path=None)
            assert len(result) == 1
            assert "002.yaml" in result
            assert "001.yaml" not in result
