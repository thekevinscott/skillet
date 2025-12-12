"""Tests for CLI module."""

import subprocess
import sys

import pytest


def describe_cli():
    """Tests for main CLI."""

    def it_shows_help():
        result = subprocess.run(
            [sys.executable, "-m", "skillet.cli.main", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "skillet" in result.stdout.lower()

    @pytest.mark.parametrize(
        "command",
        [
            "eval",
            "new",
            "tune",
            "compare",
        ],
    )
    def it_has_subcommand_help(command):
        result = subprocess.run(
            [sys.executable, "-m", "skillet.cli.main", command, "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
