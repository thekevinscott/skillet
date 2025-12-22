"""Tests for eval_command function."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from skillet.cli.commands.eval.eval import eval_command


def describe_eval_command():
    """Tests for eval_command function."""

    @pytest.fixture(autouse=True)
    def mock_console():
        """Mock console."""
        with patch("skillet.cli.commands.eval.eval.console") as mock:
            yield mock

    @pytest.fixture(autouse=True)
    def mock_load_evals():
        """Mock load_evals."""
        with patch("skillet.evals.load_evals") as mock:
            mock.return_value = [{"_source": "test.yaml"}]
            yield mock

    @pytest.fixture(autouse=True)
    def mock_live_display():
        """Mock LiveDisplay."""
        with patch("skillet.cli.commands.eval.eval.LiveDisplay") as mock_cls:
            mock_display = MagicMock()
            mock_display.start = AsyncMock()
            mock_display.stop = AsyncMock()
            mock_display.update = AsyncMock()
            mock_cls.return_value = mock_display
            yield mock_display

    @pytest.fixture(autouse=True)
    def mock_evaluate():
        """Mock evaluate function."""
        with patch("skillet.cli.commands.eval.eval.evaluate") as mock:
            mock.return_value = {
                "sampled_evals": 1,
                "total_evals": 1,
                "total_runs": 3,
                "total_pass": 2,
                "pass_rate": 66.7,
                "cached_count": 0,
                "fresh_count": 3,
                "results": [{"pass": True}, {"pass": True}, {"pass": False}],
            }
            yield mock

    @pytest.fixture(autouse=True)
    def mock_get_rate_color():
        """Mock get_rate_color."""
        with patch("skillet.cli.commands.eval.eval.get_rate_color") as mock:
            mock.return_value = "yellow"
            yield mock

    @pytest.fixture(autouse=True)
    def mock_get_scripts():
        """Mock get_scripts_from_evals."""
        with patch("skillet.cli.commands.eval.eval.get_scripts_from_evals") as mock:
            mock.return_value = []
            yield mock

    @pytest.fixture(autouse=True)
    def mock_summarize():
        """Mock summarize_responses."""
        with patch("skillet.cli.commands.eval.eval.summarize_responses") as mock:
            mock.return_value = "Test summary"
            yield mock

    @pytest.mark.asyncio
    async def it_loads_evals_by_name(mock_load_evals):
        """Loads evals using the provided name."""
        await eval_command("my-evals")
        mock_load_evals.assert_called_once_with("my-evals")

    @pytest.mark.asyncio
    async def it_runs_evaluate_with_correct_params(mock_evaluate):
        """Passes parameters to evaluate function."""
        await eval_command(
            "my-evals",
            skill_path=Path("/path/to/skill.md"),
            samples=5,
            parallel=2,
        )
        mock_evaluate.assert_called_once()
        call_kwargs = mock_evaluate.call_args.kwargs
        assert call_kwargs["skill_path"] == Path("/path/to/skill.md")
        assert call_kwargs["samples"] == 5
        assert call_kwargs["parallel"] == 2

    @pytest.mark.asyncio
    async def it_uses_get_rate_color_for_pass_rate(mock_get_rate_color):
        """Uses get_rate_color to determine pass rate color."""
        mock_get_rate_color.return_value = "green"
        await eval_command("my-evals")
        mock_get_rate_color.assert_called_with(66.7)

    @pytest.mark.asyncio
    async def it_prints_pass_rate_with_color(mock_console, mock_get_rate_color):
        """Prints pass rate using color from get_rate_color."""
        mock_get_rate_color.return_value = "red"
        await eval_command("my-evals")
        calls = [str(call) for call in mock_console.print.call_args_list]
        # Check that the pass rate line uses the color returned by get_rate_color
        assert any("red" in call and "pass rate" in call.lower() for call in calls)

    @pytest.mark.asyncio
    async def it_starts_and_stops_live_display(mock_live_display):
        """Manages live display lifecycle."""
        await eval_command("my-evals")
        mock_live_display.start.assert_called_once()
        mock_live_display.stop.assert_called_once()

    @pytest.mark.asyncio
    async def it_aborts_when_scripts_not_confirmed(mock_get_scripts, mock_evaluate):
        """Aborts if user doesn't confirm scripts."""
        mock_get_scripts.return_value = [("test.yaml", "setup", "echo test")]
        with patch("skillet.cli.commands.eval.eval.prompt_for_script_confirmation") as mock_prompt:
            mock_prompt.return_value = False
            await eval_command("my-evals")
            mock_evaluate.assert_not_called()

    @pytest.mark.asyncio
    async def it_skips_script_prompt_with_trust_flag(mock_get_scripts, mock_evaluate):
        """Skips script confirmation when trust=True."""
        mock_get_scripts.return_value = [("test.yaml", "setup", "echo test")]
        with patch("skillet.cli.commands.eval.eval.prompt_for_script_confirmation") as mock_prompt:
            await eval_command("my-evals", trust=True)
            mock_prompt.assert_not_called()
            mock_evaluate.assert_called_once()

    @pytest.mark.asyncio
    async def it_summarizes_failures(mock_summarize):
        """Calls summarize_responses when there are failures."""
        await eval_command("my-evals")
        mock_summarize.assert_called_once()
        # Should be called with the failing results
        call_args = mock_summarize.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0]["pass"] is False
