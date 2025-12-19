"""Tests for compare/run module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from skillet.compare.run import calculate_pass_rate, compare, get_cached_results_for_gap
from skillet.errors import EmptyFolderError


def describe_calculate_pass_rate():
    """Tests for calculate_pass_rate function."""

    def it_returns_none_for_empty_list():
        result = calculate_pass_rate([])
        assert result is None

    def it_calculates_100_percent_for_all_pass():
        iterations = [{"pass": True}, {"pass": True}, {"pass": True}]
        result = calculate_pass_rate(iterations)
        assert result == 100.0

    def it_calculates_0_percent_for_all_fail():
        iterations = [{"pass": False}, {"pass": False}]
        result = calculate_pass_rate(iterations)
        assert result == 0.0

    def it_calculates_partial_pass_rate():
        iterations = [{"pass": True}, {"pass": False}, {"pass": True}, {"pass": False}]
        result = calculate_pass_rate(iterations)
        assert result == 50.0

    def it_handles_missing_pass_key():
        iterations = [{"other": "data"}, {"pass": True}]
        result = calculate_pass_rate(iterations)
        assert result == 50.0


def describe_get_cached_results_for_gap():
    """Tests for get_cached_results_for_gap function."""

    def it_returns_empty_for_nonexistent_cache():
        gap = {"_source": "test.yaml", "_content": "prompt: test\nexpected: result"}
        result = get_cached_results_for_gap("nonexistent-name-12345", gap, None)
        assert result == []

    def it_uses_baseline_path_when_no_skill():
        gap = {"_source": "test.yaml", "_content": "prompt: test"}
        with patch("skillet.compare.run.CACHE_DIR", Path("/tmp/fake-cache")):
            result = get_cached_results_for_gap("myevals", gap, None)
            assert result == []

    def it_uses_skill_hash_path_when_skill_provided():
        gap = {"_source": "test.yaml", "_content": "prompt: test"}
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir)
            (skill_path / "SKILL.md").write_text("# Test skill")

            with patch("skillet.compare.run.CACHE_DIR", Path("/tmp/fake-cache")):
                result = get_cached_results_for_gap("myevals", gap, skill_path)
                assert result == []


def describe_compare():
    """Tests for compare function."""

    def it_raises_error_for_empty_evals():
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir)
            (skill_path / "SKILL.md").write_text("# Test")

            with (
                patch("skillet.compare.run.load_evals", return_value=[]),
                pytest.raises(EmptyFolderError, match=r"No evals found"),
            ):
                compare("nonexistent", skill_path)

    def it_returns_empty_results_when_no_cache():
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir)
            (skill_path / "SKILL.md").write_text("# Test")

            evals = [
                {
                    "_source": "001.yaml",
                    "_content": "prompt: test\nexpected: result",
                    "prompt": "test",
                    "expected": "result",
                }
            ]
            with (
                patch("skillet.compare.run.load_evals", return_value=evals),
                patch(
                    "skillet.compare.run.get_cached_results_for_gap", return_value=[]
                ),
            ):
                result = compare("myevals", skill_path)

                assert result["name"] == "myevals"
                assert len(result["results"]) == 1
                assert result["results"][0]["baseline"] is None
                assert result["results"][0]["skill"] is None
                assert "001.yaml" in result["missing_baseline"]
                assert "001.yaml" in result["missing_skill"]

    def it_calculates_overall_rates():
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir)
            (skill_path / "SKILL.md").write_text("# Test")

            evals = [
                {
                    "_source": "001.yaml",
                    "_content": "prompt: a\nexpected: b",
                    "prompt": "a",
                    "expected": "b",
                },
                {
                    "_source": "002.yaml",
                    "_content": "prompt: c\nexpected: d",
                    "prompt": "c",
                    "expected": "d",
                },
            ]

            def mock_cached(_name, gap, skill_path):
                # Baseline: 001 has 1 pass/1 fail, 002 has 2 pass
                # Skill: 001 has 2 pass, 002 has 1 pass/1 fail
                if skill_path is None:  # baseline
                    if gap["_source"] == "001.yaml":
                        return [{"pass": True}, {"pass": False}]
                    return [{"pass": True}, {"pass": True}]
                else:  # skill
                    if gap["_source"] == "001.yaml":
                        return [{"pass": True}, {"pass": True}]
                    return [{"pass": True}, {"pass": False}]

            with (
                patch("skillet.compare.run.load_evals", return_value=evals),
                patch(
                    "skillet.compare.run.get_cached_results_for_gap",
                    side_effect=mock_cached,
                ),
            ):
                result = compare("myevals", skill_path)

                assert result["overall_baseline"] == 75.0  # 3 pass / 4 total
                assert result["overall_skill"] == 75.0  # 3 pass / 4 total
                assert result["baseline_total"] == 4
                assert result["baseline_pass"] == 3
                assert result["skill_total"] == 4
                assert result["skill_pass"] == 3
                assert len(result["missing_baseline"]) == 0
                assert len(result["missing_skill"]) == 0

    def it_handles_mixed_cache_availability():
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir)
            (skill_path / "SKILL.md").write_text("# Test")

            evals = [
                {
                    "_source": "001.yaml",
                    "_content": "prompt: test",
                    "prompt": "test",
                    "expected": "result",
                }
            ]

            def mock_cached(_name, _gap, skill_path):
                if skill_path is None:  # baseline has results
                    return [{"pass": True}]
                return []  # skill has no results

            with (
                patch("skillet.compare.run.load_evals", return_value=evals),
                patch(
                    "skillet.compare.run.get_cached_results_for_gap",
                    side_effect=mock_cached,
                ),
            ):
                result = compare("myevals", skill_path)

                assert result["overall_baseline"] == 100.0
                assert result["overall_skill"] is None
                assert "001.yaml" not in result["missing_baseline"]
                assert "001.yaml" in result["missing_skill"]
