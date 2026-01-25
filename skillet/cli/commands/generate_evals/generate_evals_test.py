"""Tests for generate_evals_command."""

from io import StringIO
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from rich.console import Console

from skillet.generate.types import CandidateEval, GenerateResult

from .generate_evals import generate_evals_command


def _make_result(
    skill_path: Path,
    candidates: list[CandidateEval] | None = None,
) -> GenerateResult:
    return GenerateResult(
        skill_path=skill_path,
        candidates=candidates or [],
        analysis={"name": "test-skill", "goals": [], "prohibitions": [], "example_count": 0},
    )


def _make_candidate(name: str = "test") -> CandidateEval:
    return CandidateEval(
        prompt="Test",
        expected="Result",
        name=name,
        category="positive",
        source="goal:1",
        confidence=0.9,
        rationale="Test",
    )


def describe_generate_evals_command():
    """Tests for generate_evals_command function."""

    @pytest.mark.asyncio
    async def it_runs_generation_and_displays_results(tmp_path: Path):
        skill_path = tmp_path / "SKILL.md"
        skill_path.write_text("# Skill")

        output = StringIO()
        test_console = Console(file=output, force_terminal=True, force_interactive=False)

        with (
            patch(
                "skillet.cli.commands.generate_evals.generate_evals.run_generation",
                new_callable=AsyncMock,
                return_value=_make_result(skill_path),
            ),
            patch(
                "skillet.cli.commands.generate_evals.generate_evals.console",
                test_console,
            ),
            patch(
                "skillet.cli.commands.generate_evals.print_analysis_summary.console",
                test_console,
            ),
            patch(
                "skillet.cli.commands.generate_evals.print_candidates_table.console",
                test_console,
            ),
        ):
            await generate_evals_command(skill_path, dry_run=True)

        result = output.getvalue()
        assert "Skill Analysis" in result

    @pytest.mark.asyncio
    async def it_shows_dry_run_output(tmp_path: Path):
        skill_path = tmp_path / "SKILL.md"
        skill_path.write_text("# Skill")

        output = StringIO()
        test_console = Console(file=output, force_terminal=True, force_interactive=False)

        with (
            patch(
                "skillet.cli.commands.generate_evals.generate_evals.run_generation",
                new_callable=AsyncMock,
                return_value=_make_result(skill_path, [_make_candidate()]),
            ),
            patch(
                "skillet.cli.commands.generate_evals.generate_evals.console",
                test_console,
            ),
            patch(
                "skillet.cli.commands.generate_evals.print_analysis_summary.console",
                test_console,
            ),
            patch(
                "skillet.cli.commands.generate_evals.print_candidates_table.console",
                test_console,
            ),
            patch(
                "skillet.cli.commands.generate_evals.print_dry_run_output.console",
                test_console,
            ),
        ):
            await generate_evals_command(skill_path, dry_run=True)

        result = output.getvalue()
        assert "Dry run" in result

    @pytest.mark.asyncio
    async def it_shows_output_summary_when_writing(tmp_path: Path):
        skill_path = tmp_path / "SKILL.md"
        skill_path.write_text("# Skill")
        output_dir = tmp_path / "output"

        output = StringIO()
        test_console = Console(file=output, force_terminal=True, force_interactive=False)

        with (
            patch(
                "skillet.cli.commands.generate_evals.generate_evals.run_generation",
                new_callable=AsyncMock,
                return_value=_make_result(skill_path, [_make_candidate()]),
            ),
            patch(
                "skillet.cli.commands.generate_evals.generate_evals.console",
                test_console,
            ),
            patch(
                "skillet.cli.commands.generate_evals.print_analysis_summary.console",
                test_console,
            ),
            patch(
                "skillet.cli.commands.generate_evals.print_candidates_table.console",
                test_console,
            ),
            patch(
                "skillet.cli.commands.generate_evals.print_output_summary.console",
                test_console,
            ),
        ):
            await generate_evals_command(skill_path, output_dir=output_dir)

        result = output.getvalue()
        assert "Next steps" in result

    @pytest.mark.asyncio
    async def it_uses_default_output_dir_when_not_specified(tmp_path: Path):
        skill_path = tmp_path / "SKILL.md"
        skill_path.write_text("# Skill")

        output = StringIO()
        test_console = Console(file=output, force_terminal=True, force_interactive=False)

        with (
            patch(
                "skillet.cli.commands.generate_evals.generate_evals.run_generation",
                new_callable=AsyncMock,
                return_value=_make_result(skill_path),
            ) as mock_run,
            patch(
                "skillet.cli.commands.generate_evals.generate_evals.console",
                test_console,
            ),
            patch(
                "skillet.cli.commands.generate_evals.print_analysis_summary.console",
                test_console,
            ),
            patch(
                "skillet.cli.commands.generate_evals.print_candidates_table.console",
                test_console,
            ),
            patch(
                "skillet.cli.commands.generate_evals.print_output_summary.console",
                test_console,
            ),
        ):
            await generate_evals_command(skill_path)

        # Should use candidates subdirectory by default
        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["output_dir"] == tmp_path / "candidates"

    @pytest.mark.asyncio
    async def it_passes_options_to_run_generation(tmp_path: Path):
        skill_path = tmp_path / "SKILL.md"
        skill_path.write_text("# Skill")

        output = StringIO()
        test_console = Console(file=output, force_terminal=True, force_interactive=False)

        with (
            patch(
                "skillet.cli.commands.generate_evals.generate_evals.run_generation",
                new_callable=AsyncMock,
                return_value=_make_result(skill_path),
            ) as mock_run,
            patch(
                "skillet.cli.commands.generate_evals.generate_evals.console",
                test_console,
            ),
            patch(
                "skillet.cli.commands.generate_evals.print_analysis_summary.console",
                test_console,
            ),
            patch(
                "skillet.cli.commands.generate_evals.print_candidates_table.console",
                test_console,
            ),
        ):
            await generate_evals_command(
                skill_path,
                use_lint=False,
                max_per_category=3,
                dry_run=True,
            )

        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["use_lint"] is False
        assert call_kwargs["max_per_category"] == 3
        assert call_kwargs["output_dir"] is None  # dry_run=True
