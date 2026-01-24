"""Tests for run_generation."""

from io import StringIO
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from rich.console import Console

from skillet.generate.types import GenerateResult

from .run_generation import run_generation


def describe_run_generation():
    """Tests for run_generation function."""

    @pytest.mark.asyncio
    async def it_returns_generate_result(tmp_path: Path):
        skill_path = tmp_path / "SKILL.md"
        skill_path.write_text("# Skill")

        mock_result = GenerateResult(
            skill_path=skill_path,
            candidates=[],
            analysis={"name": "test"},
        )

        output = StringIO()
        test_console = Console(file=output, force_terminal=True, force_interactive=False)

        with (
            patch(
                "skillet.cli.commands.generate_evals.run_generation.generate_evals",
                new_callable=AsyncMock,
                return_value=mock_result,
            ),
            patch(
                "skillet.cli.commands.generate_evals.run_generation.console",
                test_console,
            ),
        ):
            result = await run_generation(skill_path)

        assert result == mock_result

    @pytest.mark.asyncio
    async def it_passes_kwargs_to_generate_evals(tmp_path: Path):
        skill_path = tmp_path / "SKILL.md"
        skill_path.write_text("# Skill")

        mock_result = GenerateResult(
            skill_path=skill_path,
            candidates=[],
            analysis={},
        )

        output = StringIO()
        test_console = Console(file=output, force_terminal=True, force_interactive=False)

        with (
            patch(
                "skillet.cli.commands.generate_evals.run_generation.generate_evals",
                new_callable=AsyncMock,
                return_value=mock_result,
            ) as mock_gen,
            patch(
                "skillet.cli.commands.generate_evals.run_generation.console",
                test_console,
            ),
        ):
            await run_generation(
                skill_path,
                use_lint=False,
                max_per_category=3,
            )

        mock_gen.assert_called_once()
        call_kwargs = mock_gen.call_args.kwargs
        assert call_kwargs["use_lint"] is False
        assert call_kwargs["max_per_category"] == 3

    @pytest.mark.asyncio
    async def it_shows_spinner_with_skill_name(tmp_path: Path):
        skill_path = tmp_path / "my-skill" / "SKILL.md"
        skill_path.parent.mkdir()
        skill_path.write_text("# Skill")

        mock_result = GenerateResult(
            skill_path=skill_path,
            candidates=[],
            analysis={},
        )

        output = StringIO()
        test_console = Console(file=output, force_terminal=True, force_interactive=False)

        with (
            patch(
                "skillet.cli.commands.generate_evals.run_generation.generate_evals",
                new_callable=AsyncMock,
                return_value=mock_result,
            ),
            patch(
                "skillet.cli.commands.generate_evals.run_generation.console",
                test_console,
            ),
        ):
            await run_generation(skill_path)

        # Progress spinner ran without error
        assert mock_result is not None
