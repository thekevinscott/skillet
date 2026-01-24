"""End-to-end tests for the `skillet lint` command."""

import subprocess
import sys
from pathlib import Path


def describe_skillet_lint():
    """Tests for the `skillet lint` command."""

    def it_lints_valid_skill_with_exit_code_0(tmp_path: Path):
        """Valid skill returns exit code 0."""
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test\ndescription: A test skill\n---\n\n# Instructions\n\nDo things."
        )

        result = subprocess.run(
            [sys.executable, "-m", "skillet.cli.main", "lint", str(skill_dir)],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, (
            f"Expected exit code 0, got {result.returncode}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
        assert "No issues found" in result.stdout

    def it_lints_invalid_skill_with_exit_code_1(tmp_path: Path):
        """Invalid skill returns exit code 1."""
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: test\n---\n\nMissing description.")

        result = subprocess.run(
            [sys.executable, "-m", "skillet.cli.main", "lint", str(skill_dir)],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 1, (
            f"Expected exit code 1, got {result.returncode}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
        assert "error" in result.stdout.lower()
        assert "description" in result.stdout.lower()

    def it_outputs_json_format(tmp_path: Path):
        """--format json outputs valid JSON."""
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: test\n---\n")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "skillet.cli.main",
                "lint",
                str(skill_dir),
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        import json

        data = json.loads(result.stdout)
        assert "findings" in data
        assert "summary" in data

    def it_lists_available_rules():
        """--list-rules shows available rules."""
        result = subprocess.run(
            [sys.executable, "-m", "skillet.cli.main", "lint", "--list-rules"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0
        assert "frontmatter-valid" in result.stdout

    def it_returns_exit_code_2_for_missing_path(tmp_path: Path):
        """Missing path returns exit code 2."""
        nonexistent = tmp_path / "nonexistent"

        result = subprocess.run(
            [sys.executable, "-m", "skillet.cli.main", "lint", str(nonexistent)],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 2

    def it_returns_exit_code_2_when_no_path_given():
        """No path argument returns exit code 2."""
        result = subprocess.run(
            [sys.executable, "-m", "skillet.cli.main", "lint"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 2
        assert "PATH is required" in result.stdout or "PATH is required" in result.stderr
