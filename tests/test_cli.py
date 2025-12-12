"""Tests for CLI module."""

import pytest
from click.testing import CliRunner

from skillet.cli import main


@pytest.fixture
def runner():
    return CliRunner()


def describe_cli():
    """Tests for main CLI."""

    def it_shows_help(runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "skillet" in result.output.lower()

    @pytest.mark.parametrize(
        "command",
        [
            "eval",
            "new",
            "tune",
            "compare",
        ],
    )
    def it_has_subcommand_help(runner, command):
        result = runner.invoke(main, [command, "--help"])
        assert result.exit_code == 0
