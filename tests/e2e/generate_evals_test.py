"""E2E tests for generate-evals CLI command."""

import subprocess


def test_generate_evals_shows_help():
    """CLI command exists and shows help."""
    result = subprocess.run(
        ["skillet", "generate-evals", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "generate" in result.stdout.lower()
    assert "--output" in result.stdout


def test_generate_evals_fails_for_nonexistent_path():
    """CLI fails gracefully for nonexistent skill path."""
    result = subprocess.run(
        ["skillet", "generate-evals", "/nonexistent/path"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "not found" in result.stderr.lower() or "does not exist" in result.stderr.lower()


def test_generate_evals_fails_for_missing_skill_md(tmp_path):
    """CLI fails when directory lacks SKILL.md."""
    result = subprocess.run(
        ["skillet", "generate-evals", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "skill.md" in result.stderr.lower()
