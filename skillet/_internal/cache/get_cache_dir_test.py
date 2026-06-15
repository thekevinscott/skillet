"""Tests for get_cache_dir function."""

import tempfile
from pathlib import Path

from skillet._internal.cache import get_cache_dir
from skillet.agent import Agent


def describe_get_cache_dir():
    def it_returns_baseline_when_no_skill():
        result = get_cache_dir("myevals", "eval-abc123", skill_path=None, agent=Agent.CLAUDE)
        assert "baseline" in str(result)
        assert "myevals" in str(result)
        assert "eval-abc123" in str(result)

    def it_returns_skill_hash_path_when_skill_provided():
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir)
            (skill_dir / "SKILL.md").write_text("# Test")

            result = get_cache_dir(
                "myevals", "eval-abc123", skill_path=skill_dir, agent=Agent.CLAUDE
            )
            assert "skills" in str(result)
            assert "myevals" in str(result)

    def it_includes_agent_in_path():
        claude = get_cache_dir("myevals", "eval-abc123", skill_path=None, agent=Agent.CLAUDE)
        codex = get_cache_dir("myevals", "eval-abc123", skill_path=None, agent=Agent.CODEX)
        assert "claude" in claude.parts
        assert "codex" in codex.parts
        assert claude != codex
