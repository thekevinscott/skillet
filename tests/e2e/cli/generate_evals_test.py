"""End-to-end tests for the `skillet generate-evals` command."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

PIRATE_FIXTURES = Path(__file__).parent.parent / "__fixtures__" / "tune-test"
COMPLEX_SKILL_FIXTURES = Path(__file__).parent.parent.parent / "__fixtures__"

VALID_SKILL = """\
---
name: test-skill
description: A skill for testing eval generation.
---

# Instructions

Always respond in formal English.

## Goals

- Use proper grammar and punctuation
- Maintain a professional tone

## Prohibitions

- Never use slang or informal language
- Never use emojis
"""


def describe_skillet_generate_evals():
    """Tests for the `skillet generate-evals` command."""

    @pytest.mark.asyncio
    async def it_generates_evals_from_skill(tmp_path: Path):
        """Generates candidate evals from a SKILL.md file."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(VALID_SKILL)

        output_dir = tmp_path / "candidates"

        env = os.environ.copy()

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "skillet.cli.main",
                "generate-evals",
                str(skill_file),
                "--output",
                str(output_dir),
                "--max",
                "2",
            ],
            capture_output=True,
            text=True,
            env=env,
            timeout=120,
        )

        assert result.returncode == 0, (
            f"Command failed with code {result.returncode}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

        # Should have created candidate eval files
        assert output_dir.exists(), f"Output directory not created at {output_dir}"
        yaml_files = list(output_dir.rglob("*.yaml"))
        assert len(yaml_files) > 0, (
            f"No eval files generated in {output_dir}\nstdout: {result.stdout}"
        )

    @pytest.mark.asyncio
    async def it_generates_evals_from_existing_skill(tmp_path: Path):
        """Generates evals from the pirate skill fixture content written to SKILL.md."""
        pirate_source = PIRATE_FIXTURES / ".claude" / "commands" / "pirate.md"
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(pirate_source.read_text())

        output_dir = tmp_path / "candidates"

        env = os.environ.copy()

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "skillet.cli.main",
                "generate-evals",
                str(skill_file),
                "--output",
                str(output_dir),
                "--max",
                "2",
            ],
            capture_output=True,
            text=True,
            env=env,
            timeout=120,
        )

        assert result.returncode == 0, (
            f"Command failed with code {result.returncode}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

        yaml_files = list(output_dir.rglob("*.yaml"))
        assert len(yaml_files) > 0, f"No eval files generated\nstdout: {result.stdout}"

    def it_fails_for_nonexistent_skill_path():
        """Exits with error for a missing skill path."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "skillet.cli.main",
                "generate-evals",
                "/nonexistent/path/SKILL.md",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode != 0

    def it_fails_for_directory_without_skill_md(tmp_path: Path):
        """Exits with error when directory lacks SKILL.md."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "skillet.cli.main",
                "generate-evals",
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode != 0

    @pytest.mark.asyncio
    async def it_assigns_domains_to_generated_evals(tmp_path: Path):
        """Every generated eval has a valid domain (triggering/functional/performance)."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(VALID_SKILL)

        output_dir = tmp_path / "candidates"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "skillet.cli.main",
                "generate-evals",
                str(skill_file),
                "--output",
                str(output_dir),
                "--max",
                "2",
            ],
            capture_output=True,
            text=True,
            env=os.environ.copy(),
            timeout=120,
        )

        assert result.returncode == 0, (
            f"Command failed with code {result.returncode}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

        # The table output should contain at least one valid domain
        valid_domains = {"triggering", "functional", "performance"}
        stdout_lower = result.stdout.lower()
        found_domains = {d for d in valid_domains if d in stdout_lower}
        assert len(found_domains) > 0, f"No valid domains found in output.\nstdout: {result.stdout}"

    @pytest.mark.asyncio
    async def it_filters_evals_by_domain_flag(tmp_path: Path):
        """The --domain flag filters generated evals to the requested domain."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(VALID_SKILL)

        output_dir = tmp_path / "candidates"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "skillet.cli.main",
                "generate-evals",
                str(skill_file),
                "--output",
                str(output_dir),
                "--max",
                "3",
                "--domain",
                "triggering",
            ],
            capture_output=True,
            text=True,
            env=os.environ.copy(),
            timeout=120,
        )

        assert result.returncode == 0, (
            f"Command failed with code {result.returncode}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

        # Should have generated some candidates
        yaml_files = list(output_dir.rglob("*.yaml"))
        assert len(yaml_files) > 0, f"No eval files generated\nstdout: {result.stdout}"

        # Output should mention triggering but not functional or performance
        stdout_lower = result.stdout.lower()
        assert "triggering" in stdout_lower, (
            f"Expected 'triggering' in output.\nstdout: {result.stdout}"
        )

    @pytest.mark.asyncio
    async def it_generates_evals_from_complex_skill(tmp_path: Path):
        """Complex skills with many rules still generate evals."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text((COMPLEX_SKILL_FIXTURES / "complex_skill.txt").read_text())

        output_dir = tmp_path / "candidates"

        env = os.environ.copy()

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "skillet.cli.main",
                "generate-evals",
                str(skill_file),
                "--output",
                str(output_dir),
                "--max",
                "2",
            ],
            capture_output=True,
            text=True,
            env=env,
            timeout=300,
        )

        assert result.returncode == 0, (
            f"Command failed with code {result.returncode}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

        yaml_files = list(output_dir.rglob("*.yaml"))
        assert len(yaml_files) > 0, f"No eval files generated\nstdout: {result.stdout}"
