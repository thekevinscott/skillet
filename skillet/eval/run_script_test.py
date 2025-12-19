"""Tests for eval/run_script module."""

import tempfile

from skillet.eval.run_script import run_script


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

    def it_times_out_on_hanging_script():
        """Script should be killed after timeout expires."""
        with tempfile.TemporaryDirectory() as home_dir:
            # Use a very short timeout to test the feature quickly
            returncode, _stdout, stderr = run_script("sleep 10", home_dir, timeout=1)
            assert returncode == -1
            assert "timed out" in stderr
            assert "1s" in stderr

    def it_respects_custom_timeout():
        """Script should complete if within timeout."""
        with tempfile.TemporaryDirectory() as home_dir:
            # Script runs in < 1s, timeout is 5s
            returncode, stdout, _stderr = run_script("echo fast", home_dir, timeout=5)
            assert returncode == 0
            assert "fast" in stdout
