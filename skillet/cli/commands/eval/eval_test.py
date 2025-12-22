"""Tests for eval_command function."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from skillet.cli.commands.eval.eval import eval_command


def describe_eval_command():
    """Tests for eval_command function."""

    @pytest.fixture
    def mock_deps():
        """Mock all dependencies for eval_command."""
        with (
            patch("skillet.cli.commands.eval.eval.console") as mock_console,
            patch("skillet.evals.load_evals") as mock_load_evals,
            patch("skillet.cli.commands.eval.eval.LiveDisplay") as mock_display_cls,
            patch("skillet.cli.commands.eval.eval.evaluate") as mock_evaluate,
            patch("skillet.cli.commands.eval.eval.get_rate_color") as mock_get_rate_color,
            patch(
                "skillet.cli.commands.eval.eval.get_scripts_from_evals"
            ) as mock_get_scripts,
            patch("skillet.cli.commands.eval.eval.summarize_responses") as mock_summarize,
        ):
            # Setup default mocks
            mock_load_evals.return_value = [{"_source": "test.yaml"}]
            mock_get_scripts.return_value = []
            mock_display = MagicMock()
            mock_display.start = AsyncMock()
            mock_display.stop = AsyncMock()
            mock_display.update = AsyncMock()
            mock_display_cls.return_value = mock_display
            mock_evaluate.return_value = {
                "sampled_evals": 1,
                "total_evals": 1,
                "total_runs": 3,
                "total_pass": 2,
                "pass_rate": 66.7,
                "cached_count": 0,
                "fresh_count": 3,
                "results": [{"pass": True}, {"pass": True}, {"pass": False}],
            }
            mock_get_rate_color.return_value = "yellow"
            mock_summarize.return_value = "Test summary"

            yield {
                "console": mock_console,
                "load_evals": mock_load_evals,
                "display_cls": mock_display_cls,
                "display": mock_display,
                "evaluate": mock_evaluate,
                "get_rate_color": mock_get_rate_color,
                "get_scripts": mock_get_scripts,
                "summarize": mock_summarize,
            }

    @pytest.mark.asyncio
    async def it_loads_evals_by_name(mock_deps):
        """Loads evals using the provided name."""
        await eval_command("my-evals")
        mock_deps["load_evals"].assert_called_once_with("my-evals")

    @pytest.mark.asyncio
    async def it_runs_evaluate_with_correct_params(mock_deps):
        """Passes parameters to evaluate function."""
        await eval_command(
            "my-evals",
            skill_path=Path("/path/to/skill.md"),
            samples=5,
            parallel=2,
        )
        mock_deps["evaluate"].assert_called_once()
        call_kwargs = mock_deps["evaluate"].call_args.kwargs
        assert call_kwargs["skill_path"] == Path("/path/to/skill.md")
        assert call_kwargs["samples"] == 5
        assert call_kwargs["parallel"] == 2

    @pytest.mark.asyncio
    async def it_uses_get_rate_color_for_pass_rate(mock_deps):
        """Uses get_rate_color to determine pass rate color."""
        mock_deps["get_rate_color"].return_value = "green"
        await eval_command("my-evals")
        mock_deps["get_rate_color"].assert_called_with(66.7)

    @pytest.mark.asyncio
    async def it_prints_pass_rate_with_color(mock_deps):
        """Prints pass rate using color from get_rate_color."""
        mock_deps["get_rate_color"].return_value = "red"
        await eval_command("my-evals")
        calls = [str(call) for call in mock_deps["console"].print.call_args_list]
        # Check that the pass rate line uses the color returned by get_rate_color
        assert any("red" in call and "pass rate" in call.lower() for call in calls)

    @pytest.mark.asyncio
    async def it_starts_and_stops_live_display(mock_deps):
        """Manages live display lifecycle."""
        await eval_command("my-evals")
        mock_deps["display"].start.assert_called_once()
        mock_deps["display"].stop.assert_called_once()

    @pytest.mark.asyncio
    async def it_aborts_when_scripts_not_confirmed(mock_deps):
        """Aborts if user doesn't confirm scripts."""
        mock_deps["get_scripts"].return_value = [("test.yaml", "setup", "echo test")]
        with patch(
            "skillet.cli.commands.eval.eval.prompt_for_script_confirmation"
        ) as mock_prompt:
            mock_prompt.return_value = False
            await eval_command("my-evals")
            mock_deps["evaluate"].assert_not_called()

    @pytest.mark.asyncio
    async def it_skips_script_prompt_with_trust_flag(mock_deps):
        """Skips script confirmation when trust=True."""
        mock_deps["get_scripts"].return_value = [("test.yaml", "setup", "echo test")]
        with patch(
            "skillet.cli.commands.eval.eval.prompt_for_script_confirmation"
        ) as mock_prompt:
            await eval_command("my-evals", trust=True)
            mock_prompt.assert_not_called()
            mock_deps["evaluate"].assert_called_once()

    @pytest.mark.asyncio
    async def it_summarizes_failures(mock_deps):
        """Calls summarize_responses when there are failures."""
        await eval_command("my-evals")
        mock_deps["summarize"].assert_called_once()
        # Should be called with the failing results
        call_args = mock_deps["summarize"].call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0]["pass"] is False
