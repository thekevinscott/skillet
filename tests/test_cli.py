"""Tests for CLI module."""

from click.testing import CliRunner

from skillet.cli import main


def test_cli_help():
    """CLI shows help text."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "skillet" in result.output.lower()


def test_cli_eval_help():
    """Eval command shows help."""
    runner = CliRunner()
    result = runner.invoke(main, ["eval", "--help"])
    assert result.exit_code == 0
    assert "skill" in result.output.lower()


def test_cli_new_help():
    """New command shows help."""
    runner = CliRunner()
    result = runner.invoke(main, ["new", "--help"])
    assert result.exit_code == 0


def test_cli_tune_help():
    """Tune command shows help."""
    runner = CliRunner()
    result = runner.invoke(main, ["tune", "--help"])
    assert result.exit_code == 0


def test_cli_compare_help():
    """Compare command shows help."""
    runner = CliRunner()
    result = runner.invoke(main, ["compare", "--help"])
    assert result.exit_code == 0
