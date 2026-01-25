"""Tests for generate_evals function."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from .generate_evals import generate_evals
from .types import CandidateEval, GenerateResult


def describe_generate_evals():
    """Tests for generate_evals function."""

    @pytest.mark.asyncio
    async def it_returns_generate_result(tmp_path: Path):
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("---\nname: test-skill\n---\n## Goals\n\n1. Do something useful\n")

        mock_candidates = [
            CandidateEval(
                prompt="Test prompt",
                expected="Test expected",
                name="test-eval",
                category="positive",
                source="goal:1",
                confidence=0.9,
                rationale="Testing",
            )
        ]

        with patch(
            "skillet.generate.generate_evals.generate_candidates",
            new_callable=AsyncMock,
            return_value=mock_candidates,
        ):
            result = await generate_evals(skill_file)

        assert isinstance(result, GenerateResult)
        assert result.skill_path == skill_file
        assert result.candidates == mock_candidates
        assert result.analysis["name"] == "test-skill"

    @pytest.mark.asyncio
    async def it_accepts_directory_path(tmp_path: Path):
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("# Skill")

        with patch(
            "skillet.generate.generate_evals.generate_candidates",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = await generate_evals(tmp_path)

        assert result.skill_path == skill_file

    @pytest.mark.asyncio
    async def it_writes_candidates_when_output_dir_specified(tmp_path: Path):
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("# Skill")
        output_dir = tmp_path / "output"

        mock_candidate = CandidateEval(
            prompt="Test",
            expected="Result",
            name="test",
            category="positive",
            source="test",
            confidence=0.8,
            rationale="Test",
        )

        with patch(
            "skillet.generate.generate_evals.generate_candidates",
            new_callable=AsyncMock,
            return_value=[mock_candidate],
        ):
            await generate_evals(skill_file, output_dir=output_dir)

        assert output_dir.exists()
        yaml_files = list(output_dir.glob("*.yaml"))
        assert len(yaml_files) == 1

    @pytest.mark.asyncio
    async def it_does_not_write_when_no_output_dir(tmp_path: Path):
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("# Skill")

        with patch(
            "skillet.generate.generate_evals.generate_candidates",
            new_callable=AsyncMock,
            return_value=[],
        ):
            await generate_evals(skill_file)

        # No candidates directory should be created
        assert not (tmp_path / "candidates").exists()

    @pytest.mark.asyncio
    async def it_passes_options_to_generate_candidates(tmp_path: Path):
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("# Skill")

        with patch(
            "skillet.generate.generate_evals.generate_candidates",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_gen:
            await generate_evals(
                skill_file,
                use_lint=False,
                max_per_category=3,
            )

        mock_gen.assert_called_once()
        call_kwargs = mock_gen.call_args.kwargs
        assert call_kwargs["use_lint"] is False
        assert call_kwargs["max_per_category"] == 3

    @pytest.mark.asyncio
    async def it_includes_analysis_summary(tmp_path: Path):
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            "---\n"
            "name: my-skill\n"
            "description: Test skill\n"
            "---\n"
            "## Goals\n"
            "\n"
            "1. Goal one\n"
            "2. Goal two\n"
            "\n"
            "## Prohibitions\n"
            "\n"
            "- Don't do bad things\n"
            "\n"
            "```python\n"
            "example()\n"
            "```\n"
        )

        with patch(
            "skillet.generate.generate_evals.generate_candidates",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = await generate_evals(skill_file)

        assert result.analysis["name"] == "my-skill"
        assert result.analysis["description"] == "Test skill"
        assert result.analysis["goals"] == ["Goal one", "Goal two"]
        assert result.analysis["prohibitions"] == ["Don't do bad things"]
        assert result.analysis["example_count"] == 1
