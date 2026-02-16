"""End-to-end tests for the `skillet create` command."""

import sys
from collections.abc import Callable
from pathlib import Path

import pytest
from curtaincall import Terminal, expect

from tests.e2e.helpers import add_evals

SKILLET = f"{sys.executable} -m skillet.cli.main"


def describe_skillet_create():
    """Tests for the `skillet create` command."""

    @pytest.mark.asyncio
    async def it_creates_skill_from_evals(
        terminal: Callable[..., Terminal],
        skillet_env: Path,
    ):
        """Test that skillet create creates SKILL.md from eval files."""
        add_evals(skillet_env, "browser-fallback", count=2)

        output_dir = skillet_env / "output"
        output_dir.mkdir()

        term = terminal(
            f"{SKILLET} create browser-fallback -d {output_dir}",
            env={"SKILLET_DIR": str(skillet_env / ".skillet")},
        )
        expect(term.get_by_text("skillet compare")).to_be_visible(timeout=120)

        skill_path = output_dir / ".claude" / "skills" / "browser-fallback" / "SKILL.md"
        assert skill_path.exists(), f"SKILL.md not found at {skill_path}"

        content = skill_path.read_text()
        assert len(content.strip()) > 0, "SKILL.md is empty"
        assert "---" in content, "SKILL.md should have YAML frontmatter"
