"""Tests for create command."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from skillet.cli.commands.create.create import create_command
from skillet.errors import SkillError


def describe_create_command():
    """Tests for create_command function."""

    @pytest.mark.asyncio
    async def it_creates_skill_directory():
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch("skillet.cli.commands.create.create.load_evals") as mock_load,
            patch(
                "skillet.cli.commands.create.create.create_skill",
                new_callable=AsyncMock,
            ) as mock_create,
            patch("skillet.cli.commands.create.create.console") as mock_console,
        ):
            mock_load.return_value = [
                {"_source": "eval1.yaml", "prompt": "test", "expected": "result"}
            ]
            mock_create.return_value = {
                "skill_dir": Path(tmpdir) / "my-skill",
                "eval_count": 1,
            }

            await create_command("my-skill", Path(tmpdir))

            mock_create.assert_called_once()
            # Verify output was printed
            assert mock_console.print.called

    @pytest.mark.asyncio
    async def it_raises_when_no_evals_found():
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch("skillet.cli.commands.create.create.load_evals") as mock_load,
        ):
            mock_load.return_value = []

            with pytest.raises(SkillError, match="No eval files found"):
                await create_command("my-skill", Path(tmpdir))

    @pytest.mark.asyncio
    async def it_prompts_for_overwrite_if_exists():
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch("skillet.cli.commands.create.create.load_evals") as mock_load,
            patch(
                "skillet.cli.commands.create.create.create_skill",
                new_callable=AsyncMock,
            ) as mock_create,
            patch("skillet.cli.commands.create.create.console") as mock_console,
        ):
            # Create existing skill directory
            skill_dir = Path(tmpdir) / "my-skill"
            skill_dir.mkdir()

            mock_load.return_value = [
                {"_source": "eval1.yaml", "prompt": "test", "expected": "result"}
            ]
            mock_console.input.return_value = "y"
            mock_create.return_value = {
                "skill_dir": skill_dir,
                "eval_count": 1,
            }

            await create_command("my-skill", Path(tmpdir))

            # Should have prompted for overwrite
            mock_console.input.assert_called_once()
            # Should have called create_skill with overwrite=True
            call_kwargs = mock_create.call_args[1]
            assert call_kwargs.get("overwrite") is True

    @pytest.mark.asyncio
    async def it_exits_when_overwrite_declined():
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch("skillet.cli.commands.create.create.load_evals") as mock_load,
            patch("skillet.cli.commands.create.create.console") as mock_console,
        ):
            # Create existing skill directory
            skill_dir = Path(tmpdir) / "my-skill"
            skill_dir.mkdir()

            mock_load.return_value = [
                {"_source": "eval1.yaml", "prompt": "test", "expected": "result"}
            ]
            mock_console.input.return_value = "n"

            with pytest.raises(SystemExit):
                await create_command("my-skill", Path(tmpdir))

    @pytest.mark.asyncio
    async def it_passes_extra_prompt():
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch("skillet.cli.commands.create.create.load_evals") as mock_load,
            patch(
                "skillet.cli.commands.create.create.create_skill",
                new_callable=AsyncMock,
            ) as mock_create,
            patch("skillet.cli.commands.create.create.console"),
        ):
            mock_load.return_value = [
                {"_source": "eval1.yaml", "prompt": "test", "expected": "result"}
            ]
            mock_create.return_value = {
                "skill_dir": Path(tmpdir) / "my-skill",
                "eval_count": 1,
            }

            await create_command("my-skill", Path(tmpdir), extra_prompt="Custom")

            call_args = mock_create.call_args
            assert call_args[0][2] == "Custom"  # extra_prompt is 3rd positional arg
