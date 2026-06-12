"""Tests for get_cache_dir function."""

import tempfile
from pathlib import Path

from skillet._internal.cache import get_cache_dir


def describe_get_cache_dir():
    def it_returns_baseline_when_no_skill():
        result = get_cache_dir("myevals", "eval-abc123", skill_path=None)
        assert "baseline" in str(result)
        assert "myevals" in str(result)
        assert "eval-abc123" in str(result)

    def it_returns_skill_hash_path_when_skill_provided():
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir)
            (skill_dir / "SKILL.md").write_text("# Test")

            result = get_cache_dir("myevals", "eval-abc123", skill_path=skill_dir)
            assert "skills" in str(result)
            assert "myevals" in str(result)

    def it_keeps_the_default_path_unchanged():
        default = get_cache_dir("myevals", "eval-abc123")
        explicit = get_cache_dir("myevals", "eval-abc123", launcher=None)
        assert default == explicit
        assert "launcher-" not in str(default)

    def it_namespaces_a_launcher():
        result = get_cache_dir("myevals", "eval-abc123", launcher="codex exec")
        assert "launcher-" in str(result)
        assert "baseline" in str(result)

    def it_isolates_launchers_from_each_other_and_the_default():
        default = get_cache_dir("myevals", "eval-abc123")
        codex = get_cache_dir("myevals", "eval-abc123", launcher="codex exec")
        gemini = get_cache_dir("myevals", "eval-abc123", launcher="gemini")
        assert default != codex
        assert codex != gemini
