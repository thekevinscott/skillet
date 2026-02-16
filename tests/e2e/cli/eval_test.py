"""End-to-end tests for the `skillet eval` command."""

from collections.abc import Callable
from pathlib import Path

import pytest
from curtaincall import Terminal, expect

PIRATE_FIXTURES = Path(__file__).parent.parent / "__fixtures__" / "tune-test"
SKILLET = "skillet"


def _setup_eval_env(tmp_path: Path) -> Path:
    """Set up pirate eval fixtures in a temp directory. Returns evals_dir."""
    evals_dir = tmp_path / "evals" / "pirate"
    evals_dir.mkdir(parents=True)

    pirate_evals = PIRATE_FIXTURES / "evals" / "pirate"
    for eval_file in pirate_evals.glob("*.yaml"):
        (evals_dir / eval_file.name).write_text(eval_file.read_text())

    return evals_dir


def describe_skillet_eval():
    """Tests for the `skillet eval` command."""

    @pytest.mark.asyncio
    async def it_runs_baseline_evaluation(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        """Runs eval without a skill (baseline mode)."""
        evals_dir = _setup_eval_env(tmp_path)

        term = terminal(f"{SKILLET} eval {evals_dir} --samples 1 --parallel 1 --skip-cache --trust")
        expect(term.get_by_text("Overall pass rate:")).to_be_visible(timeout=300)

    @pytest.mark.asyncio
    async def it_runs_evaluation_with_skill(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        """Runs eval with a skill file."""
        evals_dir = _setup_eval_env(tmp_path)

        skill_dir = tmp_path / "skills"
        skill_dir.mkdir()
        skill_file = skill_dir / "pirate.md"
        pirate_skill = PIRATE_FIXTURES / ".claude" / "commands" / "pirate.md"
        skill_file.write_text(pirate_skill.read_text())

        term = terminal(
            f"{SKILLET} eval {evals_dir} {skill_file} --samples 1 --parallel 1 --skip-cache --trust"
        )
        expect(term.get_by_text("Overall pass rate:")).to_be_visible(timeout=300)

    @pytest.mark.asyncio
    async def it_respects_max_evals_flag(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        """Limits evaluation to --max-evals count."""
        evals_dir = _setup_eval_env(tmp_path)

        term = terminal(
            f"{SKILLET} eval {evals_dir}"
            f" --samples 1 --max-evals 1 --parallel 1 --skip-cache --trust"
        )
        expect(term.get_by_text("Overall pass rate:")).to_be_visible(timeout=300)

    @pytest.mark.asyncio
    async def it_evaluates_single_yaml_file(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        """Runs eval on a single .yaml file path."""
        evals_dir = _setup_eval_env(tmp_path)
        single_eval = evals_dir / "001-greeting.yaml"

        term = terminal(
            f"{SKILLET} eval {single_eval} --samples 1 --parallel 1 --skip-cache --trust"
        )
        expect(term.get_by_text("Overall pass rate:")).to_be_visible(timeout=300)

    @pytest.mark.asyncio
    async def it_shows_pass_at_k_metrics_with_multiple_samples(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        """Shows pass@k and pass^k metrics when samples > 1."""
        evals_dir = _setup_eval_env(tmp_path)

        term = terminal(f"{SKILLET} eval {evals_dir} --samples 3 --parallel 1 --skip-cache --trust")
        expect(term.get_by_text("Overall pass rate:")).to_be_visible(timeout=300)
        expect(term.get_by_text("pass@3")).to_be_visible()
        expect(term.get_by_text("pass^3")).to_be_visible()

    def it_fails_for_nonexistent_eval_directory(
        terminal: Callable[..., Terminal],
    ):
        """Exits with error for a missing eval directory."""
        term = terminal(f"{SKILLET} eval /nonexistent/path/to/evals --trust")
        expect(term).to_have_exited()
        assert term.exit_code != 0
