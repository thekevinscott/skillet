"""End-to-end tests for generate-evals CLI command."""

import subprocess
from pathlib import Path

import pytest

SAMPLE_SKILL = """---
name: test-skill
description: A test skill for E2E testing
---

# Test Skill

## Goals

1. Do something useful
2. Handle edge cases

## Prohibitions

- Never do bad things
"""


def describe_generate_evals_command():
    """Tests for the `skillet generate-evals` command."""

    def it_shows_help(tmp_path: Path):
        """CLI shows help information."""
        result = subprocess.run(
            ["skillet", "generate-evals", "--help"],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )
        assert result.returncode == 0
        assert "generate-evals" in result.stdout.lower() or "skill" in result.stdout.lower()

    def it_fails_for_nonexistent_skill(tmp_path: Path):
        """CLI fails gracefully for nonexistent skill path."""
        result = subprocess.run(
            ["skillet", "generate-evals", "/nonexistent/path"],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )
        assert result.returncode != 0
        assert "not found" in result.stderr.lower() or "does not exist" in result.stderr.lower()

    def it_fails_for_directory_without_skill_md(tmp_path: Path):
        """CLI fails when directory lacks SKILL.md."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = subprocess.run(
            ["skillet", "generate-evals", str(empty_dir)],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )
        assert result.returncode != 0
        assert "skill.md" in result.stderr.lower()

    @pytest.mark.skip(reason="Requires real LLM - enable with SKILLET_E2E_LIVE=1")
    def it_generates_evals_with_dry_run(tmp_path: Path):
        """CLI generates evals in dry-run mode."""
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(SAMPLE_SKILL)

        result = subprocess.run(
            ["skillet", "generate-evals", str(skill_dir), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )
        assert result.returncode == 0
        assert "dry run" in result.stdout.lower()

    @pytest.mark.skip(reason="Requires real LLM - enable with SKILLET_E2E_LIVE=1")
    def it_generates_evals_to_output_dir(tmp_path: Path):
        """CLI generates eval files to specified output directory."""
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(SAMPLE_SKILL)

        output_dir = tmp_path / "output"

        result = subprocess.run(
            ["skillet", "generate-evals", str(skill_dir), "-o", str(output_dir)],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )
        assert result.returncode == 0
        assert output_dir.exists()
        yaml_files = list(output_dir.glob("*.yaml"))
        assert len(yaml_files) > 0

    @pytest.mark.skip(reason="Requires real LLM - enable with SKILLET_E2E_LIVE=1")
    def it_supports_max_per_category_flag(tmp_path: Path):
        """CLI --max flag limits candidates per category."""
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(SAMPLE_SKILL)

        result = subprocess.run(
            ["skillet", "generate-evals", str(skill_dir), "-m", "2", "--dry-run"],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )
        assert result.returncode == 0
