"""End-to-end tests for the `skillet compare` command."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

PIRATE_FIXTURES = Path(__file__).parent.parent / "__fixtures__" / "tune-test"


def _setup_compare_env(tmp_path: Path) -> tuple[Path, Path, dict]:
    """Set up pirate eval fixtures and skill in a temp directory."""
    evals_dir = tmp_path / "evals" / "pirate"
    evals_dir.mkdir(parents=True)

    pirate_evals = PIRATE_FIXTURES / "evals" / "pirate"
    for eval_file in pirate_evals.glob("*.yaml"):
        (evals_dir / eval_file.name).write_text(eval_file.read_text())

    skill_dir = tmp_path / "skills"
    skill_dir.mkdir()
    skill_file = skill_dir / "pirate.md"
    pirate_skill = PIRATE_FIXTURES / ".claude" / "commands" / "pirate.md"
    skill_file.write_text(pirate_skill.read_text())

    env = os.environ.copy()
    return evals_dir, skill_file, env


def describe_skillet_compare():
    """Tests for the `skillet compare` command."""

    @pytest.mark.asyncio
    async def it_compares_baseline_vs_skill(tmp_path: Path):
        """Runs eval for baseline and skill, then compares."""
        evals_dir, skill_file, env = _setup_compare_env(tmp_path)

        # Run baseline eval first
        baseline_result = subprocess.run(
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
        assert baseline_result.returncode == 0, (
            f"Baseline eval failed:\n"
            f"stdout: {baseline_result.stdout}\n"
            f"stderr: {baseline_result.stderr}"
        )

        # Run skill eval
        skill_result = subprocess.run(
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
        assert skill_result.returncode == 0, (
            f"Skill eval failed:\nstdout: {skill_result.stdout}\nstderr: {skill_result.stderr}"
        )

        # Now run compare
        compare_result = subprocess.run(
            [
                sys.executable,
                "-m",
                "skillet.cli.main",
                "compare",
                str(evals_dir),
                str(skill_file),
            ],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
        assert compare_result.returncode == 0, (
            f"Compare failed:\nstdout: {compare_result.stdout}\nstderr: {compare_result.stderr}"
        )
        # Output should contain comparison data (percentages or delta)
        assert "%" in compare_result.stdout or "overall" in compare_result.stdout.lower()

    def it_errors_when_no_eval_files_exist(tmp_path: Path):
        """Exits with error when evals directory is empty."""
        evals_dir = tmp_path / "evals" / "nonexistent-skill"
        evals_dir.mkdir(parents=True)

        skill_file = tmp_path / "skills" / "fake.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("# Fake skill")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "skillet.cli.main",
                "compare",
                str(evals_dir),
                str(skill_file),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode != 0
