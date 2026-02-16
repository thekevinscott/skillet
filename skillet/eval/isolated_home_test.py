"""Tests for eval/isolated_home module."""

import tempfile
from pathlib import Path

from skillet.eval.isolated_home import isolated_home


def describe_isolated_home():
    """Tests for isolated_home context manager."""

    def it_creates_temp_directory():
        with isolated_home() as home_dir:
            assert Path(home_dir).exists()
            assert Path(home_dir).is_dir()
            assert "skillet-eval-" in home_dir

    def it_cleans_up_after_context():
        with isolated_home() as home_dir:
            temp_path = Path(home_dir)
        # After context exits, directory should be gone
        assert not temp_path.exists()

    def it_copies_claude_files_into_real_directory(monkeypatch):
        """Root-level files from ~/.claude are copied (not symlinked)."""
        with tempfile.TemporaryDirectory() as fake_home:
            claude_dir = Path(fake_home) / ".claude"
            claude_dir.mkdir()
            (claude_dir / "config.json").write_text('{"key": "value"}')
            (claude_dir / "credentials").write_text("token123")

            monkeypatch.setenv("HOME", fake_home)
            with isolated_home() as home_dir:
                isolated_claude = Path(home_dir) / ".claude"
                assert isolated_claude.exists()
                assert isolated_claude.is_dir()
                assert not isolated_claude.is_symlink()
                # Files were copied
                assert (isolated_claude / "config.json").read_text() == '{"key": "value"}'
                assert (isolated_claude / "credentials").read_text() == "token123"

    def it_excludes_subdirectories_from_claude_copy(monkeypatch):
        """Subdirectories like commands/ and agents/ are not copied."""
        with tempfile.TemporaryDirectory() as fake_home:
            claude_dir = Path(fake_home) / ".claude"
            claude_dir.mkdir()
            (claude_dir / "config.json").write_text("{}")
            (claude_dir / "commands").mkdir()
            (claude_dir / "commands" / "cmd.py").write_text("pass")
            (claude_dir / "agents").mkdir()
            (claude_dir / "agents" / "agent.py").write_text("pass")

            monkeypatch.setenv("HOME", fake_home)
            with isolated_home() as home_dir:
                isolated_claude = Path(home_dir) / ".claude"
                assert (isolated_claude / "config.json").exists()
                assert not (isolated_claude / "commands").exists()
                assert not (isolated_claude / "agents").exists()

    def it_does_not_create_claude_dir_when_missing(monkeypatch):
        """No .claude directory is created when ~/.claude doesn't exist."""
        with tempfile.TemporaryDirectory() as fake_home:
            monkeypatch.setenv("HOME", fake_home)
            with isolated_home() as home_dir:
                isolated_claude = Path(home_dir) / ".claude"
                assert not isolated_claude.exists()
