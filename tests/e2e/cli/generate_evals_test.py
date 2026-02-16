"""End-to-end tests for the `skillet generate-evals` command."""

import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest
from curtaincall import Terminal, expect

PIRATE_FIXTURES = Path(__file__).parent.parent / "__fixtures__" / "tune-test"
COMPLEX_SKILL_FIXTURES = Path(__file__).parent.parent.parent / "__fixtures__"
SKILLET = f"{sys.executable} -m skillet.cli.main"

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
    async def it_generates_evals_from_skill(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        """Generates candidate evals from a SKILL.md file."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(VALID_SKILL)

        output_dir = tmp_path / "candidates"

        term = terminal(f"{SKILLET} generate-evals {skill_file} --output {output_dir} --max 2")
        expect(term.get_by_text("Written to")).to_be_visible(timeout=120)

        assert output_dir.exists(), f"Output directory not created at {output_dir}"
        yaml_files = list(output_dir.rglob("*.yaml"))
        assert len(yaml_files) > 0, f"No eval files generated in {output_dir}"

    @pytest.mark.asyncio
    async def it_generates_evals_from_existing_skill(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        """Generates evals from the pirate skill fixture content written to SKILL.md."""
        pirate_source = PIRATE_FIXTURES / ".claude" / "commands" / "pirate.md"
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(pirate_source.read_text())

        output_dir = tmp_path / "candidates"

        term = terminal(f"{SKILLET} generate-evals {skill_file} --output {output_dir} --max 2")
        expect(term.get_by_text("Written to")).to_be_visible(timeout=120)

        yaml_files = list(output_dir.rglob("*.yaml"))
        assert len(yaml_files) > 0, "No eval files generated"

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
    async def it_assigns_domains_to_generated_evals(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        """Every generated eval has a valid domain (triggering/functional/performance)."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(VALID_SKILL)

        output_dir = tmp_path / "candidates"

        term = terminal(f"{SKILLET} generate-evals {skill_file} --output {output_dir} --max 2")
        expect(term.get_by_text("Written to")).to_be_visible(timeout=120)

        # At least one valid domain should appear in the table output
        found = False
        for domain in ("triggering", "functional", "performance"):
            if term.get_by_text(domain).is_visible():
                found = True
                break
        assert found, "No valid domain found in output"

    @pytest.mark.asyncio
    async def it_filters_evals_by_domain_flag(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        """The --domain flag filters generated evals to the requested domain."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(VALID_SKILL)

        output_dir = tmp_path / "candidates"

        term = terminal(
            f"{SKILLET} generate-evals {skill_file}"
            f" --output {output_dir} --max 3 --domain triggering"
        )
        expect(term.get_by_text("Written to")).to_be_visible(timeout=120)

        yaml_files = list(output_dir.rglob("*.yaml"))
        assert len(yaml_files) > 0, "No eval files generated"

        expect(term.get_by_text("triggering")).to_be_visible()

    @pytest.mark.asyncio
    async def it_generates_evals_from_complex_skill(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        """Complex skills with many rules still generate evals."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text((COMPLEX_SKILL_FIXTURES / "complex_skill.txt").read_text())

        output_dir = tmp_path / "candidates"

        term = terminal(f"{SKILLET} generate-evals {skill_file} --output {output_dir} --max 2")
        expect(term.get_by_text("Written to")).to_be_visible(timeout=300)

        yaml_files = list(output_dir.rglob("*.yaml"))
        assert len(yaml_files) > 0, "No eval files generated"
