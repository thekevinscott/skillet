"""Integration tests for the compare API."""

from pathlib import Path
from unittest.mock import patch

import pytest

from skillet import compare
from skillet.errors import EmptyFolderError

from .conftest import create_eval_file


def describe_compare():
    """Integration tests for compare function."""

    @pytest.mark.asyncio
    async def it_compares_baseline_and_skill_results(skillet_env: Path):
        """Happy path: compares cached baseline and skill results."""
        evals_dir = skillet_env / ".skillet" / "evals" / "compare-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")
        create_eval_file(evals_dir / "002.yaml", prompt="Second prompt")

        # Create a skill file for the path
        skill_dir = skillet_env / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# Test Skill")

        # Mock the cache retrieval
        baseline_results = [
            {"iteration": 1, "pass": True},
            {"iteration": 2, "pass": False},
        ]
        skill_results = [
            {"iteration": 1, "pass": True},
            {"iteration": 2, "pass": True},
        ]

        with patch("skillet.compare.compare.get_cached_results_for_eval") as mock_cache:
            # Return baseline results for None skill_path, skill results otherwise
            def cache_side_effect(_name, _eval_item, skill_path):
                if skill_path is None:
                    return baseline_results
                return skill_results

            mock_cache.side_effect = cache_side_effect

            result = compare("compare-test", skill_file)

        assert result["name"] == "compare-test"
        assert result["overall_baseline"] == 50.0  # 1/2 pass
        assert result["overall_skill"] == 100.0  # 2/2 pass
        assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def it_reports_missing_baseline_cache(skillet_env: Path):
        """Reports when baseline cache is missing."""
        evals_dir = skillet_env / ".skillet" / "evals" / "missing-baseline"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        skill_dir = skillet_env / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# Test Skill")

        with patch("skillet.compare.compare.get_cached_results_for_eval") as mock_cache:
            # Return empty for baseline, results for skill
            def cache_side_effect(_name, _eval_item, skill_path):
                if skill_path is None:
                    return []  # No baseline cache
                return [{"iteration": 1, "pass": True}]

            mock_cache.side_effect = cache_side_effect

            result = compare("missing-baseline", skill_file)

        assert len(result["missing_baseline"]) == 1
        assert result["overall_baseline"] is None

    @pytest.mark.asyncio
    async def it_reports_missing_skill_cache(skillet_env: Path):
        """Reports when skill cache is missing."""
        evals_dir = skillet_env / ".skillet" / "evals" / "missing-skill"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        skill_dir = skillet_env / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# Test Skill")

        with patch("skillet.compare.compare.get_cached_results_for_eval") as mock_cache:
            # Return results for baseline, empty for skill
            def cache_side_effect(_name, _eval_item, skill_path):
                if skill_path is None:
                    return [{"iteration": 1, "pass": True}]
                return []  # No skill cache

            mock_cache.side_effect = cache_side_effect

            result = compare("missing-skill", skill_file)

        assert len(result["missing_skill"]) == 1
        assert result["overall_skill"] is None

    @pytest.mark.asyncio
    async def it_raises_error_for_nonexistent_evals(skillet_env: Path):
        """Raises EmptyFolderError for missing eval directory."""
        skill_file = skillet_env / "SKILL.md"
        skill_file.write_text("# Test")

        with pytest.raises(EmptyFolderError):
            compare("nonexistent", skill_file)

    @pytest.mark.asyncio
    async def it_calculates_per_eval_pass_rates(skillet_env: Path):
        """Calculates pass rates for individual evals."""
        evals_dir = skillet_env / ".skillet" / "evals" / "per-eval"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")
        create_eval_file(evals_dir / "002.yaml", prompt="Different prompt")

        skill_file = skillet_env / "SKILL.md"
        skill_file.write_text("# Test")

        with patch("skillet.compare.compare.get_cached_results_for_eval") as mock_cache:

            def cache_side_effect(_name, eval_item, skill_path):
                # Different results for different evals
                if "001" in eval_item["_source"]:
                    if skill_path is None:
                        return [{"iteration": 1, "pass": False}]
                    return [{"iteration": 1, "pass": True}]
                else:
                    if skill_path is None:
                        return [{"iteration": 1, "pass": True}]
                    return [{"iteration": 1, "pass": True}]

            mock_cache.side_effect = cache_side_effect

            result = compare("per-eval", skill_file)

        # Verify per-eval results are present
        assert len(result["results"]) == 2
        # Each result should have baseline and skill pass rates
        for r in result["results"]:
            assert "baseline" in r
            assert "skill" in r
