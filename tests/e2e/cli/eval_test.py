"""End-to-end tests for the `skillet eval` command."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

PIRATE_FIXTURES = Path(__file__).parent.parent / "__fixtures__" / "tune-test"


def _setup_eval_env(tmp_path: Path) -> tuple[Path, dict]:
    """Set up pirate eval fixtures in a temp directory. Returns (evals_dir, env)."""
    evals_dir = tmp_path / "evals" / "pirate"
    evals_dir.mkdir(parents=True)

    pirate_evals = PIRATE_FIXTURES / "evals" / "pirate"
    for eval_file in pirate_evals.glob("*.yaml"):
        (evals_dir / eval_file.name).write_text(eval_file.read_text())

    env = os.environ.copy()
    return evals_dir, env


def describe_skillet_eval():
    """Tests for the `skillet eval` command."""

    @pytest.mark.asyncio
    async def it_runs_baseline_evaluation(tmp_path: Path):
        """Runs eval without a skill (baseline mode)."""
        evals_dir, env = _setup_eval_env(tmp_path)

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "skillet.cli.main",
                "eval",
                str(evals_dir),
                "--samples",
                "1",
                "--parallel",
                "1",
                "--skip-cache",
                "--trust",
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
        # Should show pass rate in output
        assert "pass" in result.stdout.lower() or "%" in result.stdout

    @pytest.mark.asyncio
    async def it_runs_evaluation_with_skill(tmp_path: Path):
        """Runs eval with a skill file."""
        evals_dir, env = _setup_eval_env(tmp_path)

        # Copy skill file
        skill_dir = tmp_path / "skills"
        skill_dir.mkdir()
        skill_file = skill_dir / "pirate.md"
        pirate_skill = PIRATE_FIXTURES / ".claude" / "commands" / "pirate.md"
        skill_file.write_text(pirate_skill.read_text())

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "skillet.cli.main",
                "eval",
                str(evals_dir),
                str(skill_file),
                "--samples",
                "1",
                "--parallel",
                "1",
                "--skip-cache",
                "--trust",
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
        assert "pass" in result.stdout.lower() or "%" in result.stdout

    @pytest.mark.asyncio
    async def it_respects_max_evals_flag(tmp_path: Path):
        """Limits evaluation to --max-evals count."""
        evals_dir, env = _setup_eval_env(tmp_path)

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "skillet.cli.main",
                "eval",
                str(evals_dir),
                "--samples",
                "1",
                "--max-evals",
                "1",
                "--parallel",
                "1",
                "--skip-cache",
                "--trust",
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
        # With max-evals=1, should only run 1 eval
        assert "1" in result.stdout

    @pytest.mark.asyncio
    async def it_evaluates_single_yaml_file(tmp_path: Path):
        """Runs eval on a single .yaml file path."""
        evals_dir, env = _setup_eval_env(tmp_path)
        single_eval = evals_dir / "001-greeting.yaml"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "skillet.cli.main",
                "eval",
                str(single_eval),
                "--samples",
                "1",
                "--parallel",
                "1",
                "--skip-cache",
                "--trust",
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

    def it_fails_for_nonexistent_eval_directory():
        """Exits with error for a missing eval directory."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "skillet.cli.main",
                "eval",
                "/nonexistent/path/to/evals",
                "--trust",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode != 0
