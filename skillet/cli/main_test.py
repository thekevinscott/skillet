"""Tests for cli/main module."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from skillet.cli.main import app, compare, create, eval, main, tune


def describe_app():
    """Tests for CLI app structure."""

    def it_has_name():
        assert app.name == ("skillet",)

    def it_has_registered_commands():
        # Check that commands are registered
        assert hasattr(app, "_registered_commands")

    def it_has_eval_command():
        # Check eval command exists - Commands are registered as function objects
        assert len(app._registered_commands) > 0

    def it_has_multiple_commands():
        # Should have at least create, eval, tune, compare commands
        assert len(app._registered_commands) >= 4


def describe_eval_command():
    """Tests for eval CLI command."""

    @pytest.mark.asyncio
    async def it_calls_eval_command_with_defaults():
        with patch(
            "skillet.cli.commands.eval.eval_command",
            new_callable=AsyncMock,
        ) as mock_cmd:
            await eval("my-evals")

            mock_cmd.assert_called_once()
            call_kwargs = mock_cmd.call_args[1]
            assert call_kwargs["samples"] == 3
            assert call_kwargs["parallel"] == 3
            assert call_kwargs["skip_cache"] is False

    @pytest.mark.asyncio
    async def it_parses_tools_string():
        with patch(
            "skillet.cli.commands.eval.eval_command",
            new_callable=AsyncMock,
        ) as mock_cmd:
            await eval("my-evals", tools="Read,Write,Bash")

            call_kwargs = mock_cmd.call_args[1]
            assert call_kwargs["allowed_tools"] == ["Read", "Write", "Bash"]


def describe_compare_command():
    """Tests for compare CLI command."""

    def it_calls_compare_command():
        with patch("skillet.cli.commands.compare.compare_command") as mock_cmd:
            compare("my-evals", Path("/skill"))

            mock_cmd.assert_called_once_with("my-evals", Path("/skill"))


def describe_tune_command():
    """Tests for tune CLI command."""

    @pytest.mark.asyncio
    async def it_calls_tune_command_with_defaults():
        with patch(
            "skillet.cli.commands.tune.tune_command",
            new_callable=AsyncMock,
        ) as mock_cmd:
            await tune("my-evals", Path("/skill"))

            mock_cmd.assert_called_once()
            call_kwargs = mock_cmd.call_args[1]
            assert call_kwargs["max_rounds"] == 5
            assert call_kwargs["target_pass_rate"] == 100.0


def describe_create_command():
    """Tests for create CLI command."""

    @pytest.mark.asyncio
    async def it_calls_create_command_with_home_default():
        with patch(
            "skillet.cli.commands.create.create_command",
            new_callable=AsyncMock,
        ) as mock_cmd:
            await create("my-skill")

            mock_cmd.assert_called_once()
            call_kwargs = mock_cmd.call_args[1]
            # Output dir should include .claude/skills
            assert ".claude" in str(call_kwargs["output_dir"])
            assert "skills" in str(call_kwargs["output_dir"])


def _get_param_line(help_text: str, long_flag: str) -> str:
    """Extract the parameter table line for a given long flag from help output."""
    for line in help_text.splitlines():
        if long_flag in line:
            return line
    raise ValueError(f"{long_flag} not found in help output")


def describe_short_flag_uniqueness():
    """Each short flag letter has a single consistent meaning across commands."""

    @pytest.fixture
    def help_output():
        """Get --help output for each command."""
        commands = ["eval", "tune", "create", "generate-evals"]
        outputs = {}
        for cmd in commands:
            result = subprocess.run(
                [sys.executable, "-m", "skillet.cli.main", cmd, "--help"],
                capture_output=True,
                text=True,
            )
            outputs[cmd] = result.stdout
        return outputs

    def it_reserves_t_for_target_on_tune(help_output):
        """-t means --target on tune; --tools on eval has no short flag."""
        assert " -t" in _get_param_line(help_output["tune"], "--target")
        assert " -t" not in _get_param_line(help_output["eval"], "--tools")

    def it_reserves_p_for_parallel(help_output):
        """-p means --parallel on eval/tune; --prompt on create has no short flag."""
        assert " -p" in _get_param_line(help_output["eval"], "--parallel")
        assert " -p" in _get_param_line(help_output["tune"], "--parallel")
        assert " -p" not in _get_param_line(help_output["create"], "--prompt")

    def it_reserves_m_for_max_evals(help_output):
        """-m means --max-evals on eval; --max on generate-evals has no short flag."""
        assert " -m" in _get_param_line(help_output["eval"], "--max-evals")
        assert " -m" not in _get_param_line(help_output["generate-evals"], "--max ")


def describe_main_function():
    """Tests for main() entry point."""

    def it_calls_app():
        with patch("skillet.cli.main.app") as mock_app:
            main()
            mock_app.assert_called_once()
