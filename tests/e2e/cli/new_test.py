"""End-to-end tests for the `skillet new` command."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.e2e.helpers import add_evals


def describe_skillet_new():
    """Tests for the `skillet new` command."""

    @pytest.mark.asyncio
    async def it_creates_skill_from_evals(skillet_env: Path):
        """Test that skillet new creates SKILL.md from eval files."""
        # Setup: Create minimal eval fixtures
        add_evals(skillet_env, "browser-fallback", count=2)

        # Output directory
        output_dir = skillet_env / "output"
        output_dir.mkdir()

        # Run CLI with SKILLET_DIR pointing to test directory
        env = os.environ.copy()
        env["SKILLET_DIR"] = str(skillet_env / ".skillet")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "skillet.cli.main",
                "new",
                "browser-fallback",
                "-d",
                str(output_dir),
            ],
            capture_output=True,
            text=True,
            env=env,
            timeout=120,  # Allow time for Claude API call
        )

        # Assertions
        assert result.returncode == 0, (
            f"Command failed with code {result.returncode}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

        skill_path = output_dir / ".claude" / "skills" / "browser-fallback" / "SKILL.md"
        assert skill_path.exists(), f"SKILL.md not found at {skill_path}"

        content = skill_path.read_text()
        assert len(content.strip()) > 0, "SKILL.md is empty"
        assert "---" in content, "SKILL.md should have YAML frontmatter"
