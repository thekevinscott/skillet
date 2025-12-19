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

    def it_symlinks_claude_dir_if_exists(monkeypatch):
        with tempfile.TemporaryDirectory() as fake_home:
            # Create a fake .claude directory
            claude_dir = Path(fake_home) / ".claude"
            claude_dir.mkdir()
            (claude_dir / "config.json").write_text("{}")

            monkeypatch.setenv("HOME", fake_home)
            with isolated_home() as home_dir:
                isolated_claude = Path(home_dir) / ".claude"
                assert isolated_claude.exists()
                assert isolated_claude.is_symlink()
                assert isolated_claude.resolve() == claude_dir.resolve()

    def it_does_not_create_symlink_when_claude_dir_missing(monkeypatch):
        """Test that no symlink is created when ~/.claude doesn't exist."""
        with tempfile.TemporaryDirectory() as fake_home:
            # Do NOT create a .claude directory
            monkeypatch.setenv("HOME", fake_home)
            with isolated_home() as home_dir:
                isolated_claude = Path(home_dir) / ".claude"
                # Should not exist since there's no real .claude to link to
                assert not isolated_claude.exists()
