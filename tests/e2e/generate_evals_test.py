"""E2E tests for generate-evals CLI command."""

import subprocess
import sys


def test_generate_evals_shows_help():
    """CLI command exists and shows help."""
    result = subprocess.run(
        [sys.executable, "-m", "skillet.cli.main", "generate-evals", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "generate" in result.stdout.lower()
    assert "--dry-run" in result.stdout or "--output" in result.stdout
