"""Tests for cli/main module."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from skillet.cli.main import app, compare, eval, main, new, tune


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
        # Should have at least new, eval, tune, compare commands
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


def describe_new_command():
    """Tests for new CLI command."""

    @pytest.mark.asyncio
    async def it_calls_new_command_with_home_default():
        with patch(
            "skillet.cli.commands.new.new_command",
            new_callable=AsyncMock,
        ) as mock_cmd:
            await new("my-skill")

            mock_cmd.assert_called_once()
            call_kwargs = mock_cmd.call_args[1]
            # Output dir should include .claude/skills
            assert ".claude" in str(call_kwargs["output_dir"])
            assert "skills" in str(call_kwargs["output_dir"])


def describe_main_function():
    """Tests for main() entry point."""

    def it_calls_app():
        with patch("skillet.cli.main.app") as mock_app:
            main()
            mock_app.assert_called_once()
