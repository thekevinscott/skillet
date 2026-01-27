"""Integration tests for the generate_evals API."""

from pathlib import Path
from unittest.mock import patch

import pytest

from skillet.evals.load import REQUIRED_EVAL_FIELDS, load_evals

from .__fixtures__.generate_evals import SAMPLE_GENERATED_EVALS, SAMPLE_SKILL


def describe_generate_evals():
    """Integration tests for generate_evals function."""

    @pytest.mark.asyncio
    async def it_generates_evals_from_valid_skill(tmp_path: Path, mock_claude_query):
        """Happy path: generates candidate evals from a SKILL.md."""
        from skillet import generate_evals

        # Setup skill file
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(SAMPLE_SKILL)

        mock_claude_query.set_structured_response(SAMPLE_GENERATED_EVALS)

        result = await generate_evals(skill_dir)

        assert len(result.candidates) > 0
        assert all(c.name for c in result.candidates)
        assert all(c.prompt for c in result.candidates)
        assert all(c.expected for c in result.candidates)

    @pytest.mark.asyncio
    async def it_writes_candidate_files_to_output_dir(tmp_path: Path, mock_claude_query):
        """Candidates are written as YAML files."""
        from skillet import generate_evals

        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(SAMPLE_SKILL)

        output_dir = tmp_path / "output"
        mock_claude_query.set_structured_response(SAMPLE_GENERATED_EVALS)

        result = await generate_evals(skill_dir, output_dir=output_dir)

        # Check files were written
        assert output_dir.exists()
        yaml_files = list(output_dir.glob("*.yaml"))
        assert len(yaml_files) == len(result.candidates)

    @pytest.mark.asyncio
    async def it_generates_positive_and_negative_evals(tmp_path: Path, mock_claude_query):
        """Generates both happy-path and should-not-trigger cases."""
        from skillet import generate_evals

        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(SAMPLE_SKILL)

        mock_claude_query.set_structured_response(SAMPLE_GENERATED_EVALS)

        result = await generate_evals(skill_dir)

        categories = {c.category for c in result.candidates}
        assert "positive" in categories
        assert "negative" in categories

    @pytest.mark.asyncio
    async def it_integrates_with_linter_when_available(tmp_path: Path, mock_claude_query):
        """Uses lint findings to target weak spots when linter is available."""
        from skillet import generate_evals

        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(SAMPLE_SKILL)

        # Mock lint module being available
        mock_lint_result = {
            "candidates": [
                {
                    "prompt": "Test vague language case",
                    "expected": "Clarifies ambiguous instruction",
                    "name": "lint-vague-line5",
                    "category": "ambiguity",
                    "source": "lint:vague-language:5",
                    "confidence": 0.7,
                    "rationale": "Tests handling of vague language found by linter",
                },
            ]
        }
        mock_claude_query.set_structured_response(mock_lint_result)

        # Mock _try_lint to return lint findings
        mock_findings = [
            {
                "rule_id": "vague-language",
                "message": "Vague language: 'appropriately'",
                "severity": "warning",
                "line": 5,
                "suggestion": "Be more specific",
            }
        ]

        with patch("skillet.generate.generate._try_lint", return_value=mock_findings):
            result = await generate_evals(skill_dir, use_lint=True)

        # Should have lint-based candidates
        lint_sources = [c.source for c in result.candidates if c.source.startswith("lint:")]
        assert len(lint_sources) > 0

    @pytest.mark.asyncio
    async def it_works_without_linter_module(tmp_path: Path, mock_claude_query):
        """Gracefully degrades when skillet.lint is not importable."""
        from skillet import generate_evals

        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(SAMPLE_SKILL)

        mock_claude_query.set_structured_response(SAMPLE_GENERATED_EVALS)

        # Even if lint module import fails, should still work
        with patch("skillet.generate.generate._try_lint", return_value=None):
            result = await generate_evals(skill_dir, use_lint=True)

        # Should still get candidates from static analysis
        assert len(result.candidates) > 0

    @pytest.mark.asyncio
    async def it_respects_max_per_category(tmp_path: Path, mock_claude_query):
        """Limits evals per category to max_per_category."""
        from skillet import generate_evals

        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(SAMPLE_SKILL)

        # Return many candidates
        many_candidates = {
            "candidates": [
                {
                    "prompt": f"Test prompt {i}",
                    "expected": "Expected behavior",
                    "name": f"test-{i}",
                    "category": "positive",
                    "source": "goal:1",
                    "confidence": 0.8,
                    "rationale": "Test case",
                }
                for i in range(10)
            ]
        }
        mock_claude_query.set_structured_response(many_candidates)

        result = await generate_evals(skill_dir, max_per_category=3)

        # Count by category
        positive_count = sum(1 for c in result.candidates if c.category == "positive")
        assert positive_count <= 3

    @pytest.mark.asyncio
    async def it_handles_skill_path_as_file(tmp_path: Path, mock_claude_query):
        """Accepts path to SKILL.md file directly."""
        from skillet import generate_evals

        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(SAMPLE_SKILL)

        mock_claude_query.set_structured_response(SAMPLE_GENERATED_EVALS)

        # Pass file path instead of directory
        result = await generate_evals(skill_file)

        assert len(result.candidates) > 0

    @pytest.mark.asyncio
    async def it_handles_skill_path_as_directory(tmp_path: Path, mock_claude_query):
        """Accepts path to directory containing SKILL.md."""
        from skillet import generate_evals

        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(SAMPLE_SKILL)

        mock_claude_query.set_structured_response(SAMPLE_GENERATED_EVALS)

        result = await generate_evals(skill_dir)

        assert len(result.candidates) > 0

    @pytest.mark.asyncio
    async def it_raises_error_for_nonexistent_skill(tmp_path: Path):
        """Error: nonexistent skill path raises SkillError."""
        from skillet import generate_evals
        from skillet.errors import SkillError

        nonexistent = tmp_path / "nonexistent"

        with pytest.raises(SkillError, match=r"not found|does not exist"):
            await generate_evals(nonexistent)

    @pytest.mark.asyncio
    async def it_raises_error_for_directory_without_skill_md(tmp_path: Path):
        """Error: directory without SKILL.md raises SkillError."""
        from skillet import generate_evals
        from skillet.errors import SkillError

        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with pytest.raises(SkillError, match=r"SKILL\.md"):
            await generate_evals(empty_dir)

    @pytest.mark.asyncio
    async def it_includes_analysis_in_result(tmp_path: Path, mock_claude_query):
        """Result includes extracted analysis (goals, prohibitions)."""
        from skillet import generate_evals

        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(SAMPLE_SKILL)

        mock_claude_query.set_structured_response(SAMPLE_GENERATED_EVALS)

        result = await generate_evals(skill_dir)

        # Analysis should be populated
        assert result.analysis is not None
        assert "goals" in result.analysis or "prohibitions" in result.analysis

    @pytest.mark.asyncio
    async def it_uses_mock_not_real_api(tmp_path: Path, mock_claude_query):
        """Canary test: verify we're using mocked responses, not real API."""
        from skillet import generate_evals

        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(SAMPLE_SKILL)

        unique_marker = "UNIQUE_MOCK_MARKER_12345"
        mock_claude_query.set_structured_response(
            {
                "candidates": [
                    {
                        "prompt": unique_marker,
                        "expected": "test",
                        "name": "test",
                        "category": "positive",
                        "source": "goal:1",
                        "confidence": 0.9,
                        "rationale": "test",
                    }
                ]
            }
        )

        result = await generate_evals(skill_dir)

        # If this marker appears, we know the mock is being used
        prompts = [c.prompt for c in result.candidates]
        assert unique_marker in prompts, "Mock response not found - real API may have been called!"

    @pytest.mark.asyncio
    async def it_produces_files_loadable_by_eval_loader(tmp_path: Path, mock_claude_query):
        """Round-trip: generate -> write -> load succeeds with valid eval files."""
        from skillet import generate_evals

        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(SAMPLE_SKILL)

        output_dir = tmp_path / "output"
        mock_claude_query.set_structured_response(SAMPLE_GENERATED_EVALS)

        result = await generate_evals(skill_dir, output_dir=output_dir)

        # Round-trip: load the written files back through the eval loader
        loaded = load_evals(str(output_dir))

        assert len(loaded) == len(result.candidates)

        # Every loaded eval must have all required fields
        for eval_data in loaded:
            assert set(eval_data.keys()) >= REQUIRED_EVAL_FIELDS

        # Each candidate's name should appear in the loaded evals
        loaded_names = {e["name"] for e in loaded}
        candidate_names = {c.name for c in result.candidates}
        assert loaded_names == candidate_names

        # Prompts should match too
        loaded_prompts = {e["prompt"] for e in loaded}
        candidate_prompts = {c.prompt for c in result.candidates}
        assert loaded_prompts == candidate_prompts
