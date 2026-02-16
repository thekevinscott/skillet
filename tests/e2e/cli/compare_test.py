"""End-to-end tests for the `skillet compare` command."""

from collections.abc import Callable
from pathlib import Path

import pytest
from curtaincall import Terminal, expect

PIRATE_FIXTURES = Path(__file__).parent.parent / "__fixtures__" / "tune-test"
SKILLET = "skillet"


def _setup_compare_env(tmp_path: Path) -> tuple[Path, Path]:
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

    return evals_dir, skill_file


def describe_skillet_compare():
    """Tests for the `skillet compare` command."""

    @pytest.mark.asyncio
    async def it_compares_baseline_vs_skill(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        """Runs eval for baseline and skill, then compares."""
        evals_dir, skill_file = _setup_compare_env(tmp_path)

        # Run baseline eval first
        term = terminal(f"{SKILLET} eval {evals_dir} --samples 1 --parallel 1 --skip-cache --trust")
        expect(term.get_by_text("Overall pass rate:")).to_be_visible(timeout=300)

        # Run skill eval
        term = terminal(
            f"{SKILLET} eval {evals_dir} {skill_file} --samples 1 --parallel 1 --skip-cache --trust"
        )
        expect(term.get_by_text("Overall pass rate:")).to_be_visible(timeout=300)

        # Now run compare
        term = terminal(f"{SKILLET} compare {evals_dir} {skill_file}")
        expect(term.get_by_text("Comparison:")).to_be_visible(timeout=30)

    def it_errors_when_no_eval_files_exist(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        """Exits with error when evals directory is empty."""
        evals_dir = tmp_path / "evals" / "nonexistent-skill"
        evals_dir.mkdir(parents=True)

        skill_file = tmp_path / "skills" / "fake.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("# Fake skill")

        term = terminal(f"{SKILLET} compare {evals_dir} {skill_file}")
        expect(term).to_have_exited()
        assert term.exit_code != 0
