"""Tests for eval/run module."""

import os
import tempfile
from pathlib import Path

from skillet.eval.run import isolated_home, run_script


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

    def it_symlinks_claude_dir_if_exists():
        with tempfile.TemporaryDirectory() as fake_home:
            # Create a fake .claude directory
            claude_dir = Path(fake_home) / ".claude"
            claude_dir.mkdir()
            (claude_dir / "config.json").write_text("{}")

            original_home = os.environ.get("HOME", "")
            try:
                os.environ["HOME"] = fake_home
                with isolated_home() as home_dir:
                    isolated_claude = Path(home_dir) / ".claude"
                    assert isolated_claude.exists()
                    assert isolated_claude.is_symlink()
                    assert isolated_claude.resolve() == claude_dir.resolve()
            finally:
                os.environ["HOME"] = original_home


def describe_run_script():
    """Tests for run_script function."""

    def it_runs_simple_script():
        with tempfile.TemporaryDirectory() as home_dir:
            returncode, stdout, _stderr = run_script("echo hello", home_dir)
            assert returncode == 0
            assert "hello" in stdout

    def it_uses_provided_home_dir():
        with tempfile.TemporaryDirectory() as home_dir:
            returncode, stdout, _stderr = run_script("echo $HOME", home_dir)
            assert returncode == 0
            assert home_dir in stdout

    def it_captures_stderr():
        with tempfile.TemporaryDirectory() as home_dir:
            returncode, _stdout, stderr = run_script("echo error >&2", home_dir)
            assert returncode == 0
            assert "error" in stderr

    def it_returns_nonzero_for_failed_script():
        with tempfile.TemporaryDirectory() as home_dir:
            returncode, _stdout, _stderr = run_script("exit 1", home_dir)
            assert returncode == 1

    def it_uses_cwd_when_provided():
        with (
            tempfile.TemporaryDirectory() as home_dir,
            tempfile.TemporaryDirectory() as cwd,
        ):
            returncode, stdout, _stderr = run_script("pwd", home_dir, cwd)
            assert returncode == 0
            assert cwd in stdout
