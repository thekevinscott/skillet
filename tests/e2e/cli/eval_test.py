"""End-to-end tests for the `skillet eval` command."""

import re
from collections.abc import Callable
from pathlib import Path

import pytest
from curtaincall import Terminal, expect

PIRATE_FIXTURES = Path(__file__).parent.parent / "__fixtures__" / "tune-test"
SKILLET = "skillet"

PIRATE_PROMPTS = [
    "Say hello to me",
    "Tell me about the weather",
    "Give me directions to the store",
    "Describe a sunset",
    "Tell me a joke",
    "Explain how to tie a knot",
    "Describe your favorite food",
    "Tell me about the ocean",
    "Give me advice on sailing",
    "Describe a treasure map",
    "Tell me about parrots",
    "Explain the rules of the sea",
]


def _setup_eval_env(tmp_path: Path) -> Path:
    """Set up pirate eval fixtures in a temp directory. Returns evals_dir."""
    evals_dir = tmp_path / "evals" / "pirate"
    evals_dir.mkdir(parents=True)

    pirate_evals = PIRATE_FIXTURES / "evals" / "pirate"
    for eval_file in pirate_evals.glob("*.yaml"):
        (evals_dir / eval_file.name).write_text(eval_file.read_text())

    return evals_dir


def _setup_many_evals(tmp_path: Path, count: int = 12) -> Path:
    """Create many simple pirate eval files for compact display testing."""
    evals_dir = tmp_path / "evals" / "many-pirate"
    evals_dir.mkdir(parents=True)

    for i in range(count):
        prompt = PIRATE_PROMPTS[i % len(PIRATE_PROMPTS)]
        eval_file = evals_dir / f"{i + 1:03d}-pirate-{i + 1}.yaml"
        eval_file.write_text(
            f"timestamp: 2025-01-02T00:00:00Z\n"
            f'prompt: "/pirate {prompt}"\n'
            f'expected: "Response uses pirate language"\n'
            f"name: pirate\n"
        )

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

    @pytest.mark.asyncio
    async def it_shows_compact_display_when_evals_exceed_terminal_height(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        """Switches to compact summary when too many evals for terminal height."""
        evals_dir = _setup_many_evals(tmp_path, count=12)

        skill_dir = tmp_path / "skills"
        skill_dir.mkdir()
        skill_file = skill_dir / "pirate.md"
        pirate_skill = PIRATE_FIXTURES / ".claude" / "commands" / "pirate.md"
        skill_file.write_text(pirate_skill.read_text())

        # Use a small terminal so 12 evals can't fit as individual rows
        term = terminal(
            f"{SKILLET} eval {evals_dir} {skill_file}"
            f" --samples 1 --parallel 3 --skip-cache --trust",
            rows=15,
        )

        # Compact mode should show a summary with eval count instead of per-eval rows
        expect(term.get_by_text(re.compile(r"\d+ evals"))).to_be_visible(timeout=300)
        expect(term.get_by_text("Overall pass rate:")).to_be_visible(timeout=300)

    @pytest.mark.asyncio
    async def it_evaluates_with_code_assertions(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        """Runs eval with code-based assertions instead of LLM judge."""
        evals_dir = tmp_path / "evals" / "assertions"
        evals_dir.mkdir(parents=True)

        # Create a skill that always says "Ahoy" in pirate style
        skill_dir = tmp_path / "skills"
        skill_dir.mkdir()
        skill_file = skill_dir / "pirate.md"
        pirate_skill = PIRATE_FIXTURES / ".claude" / "commands" / "pirate.md"
        skill_file.write_text(pirate_skill.read_text())

        # Eval with assertions: checks the response contains pirate-like language
        eval_file = evals_dir / "001-greeting.yaml"
        eval_file.write_text(
            "timestamp: 2025-01-02T00:00:00Z\n"
            'prompt: "/pirate Say hello"\n'
            'expected: "Response uses pirate language"\n'
            "name: pirate\n"
            "assertions:\n"
            "  - type: regex\n"
            '    value: "(?i)(ahoy|arr|matey|ye|pirate|sail|sea|ship|captain)"\n'
        )

        term = terminal(
            f"{SKILLET} eval {evals_dir} {skill_file} --samples 1 --parallel 1 --skip-cache --trust"
        )
        expect(term.get_by_text("Overall pass rate:")).to_be_visible(timeout=300)

    def it_fails_for_nonexistent_eval_directory(
        terminal: Callable[..., Terminal],
    ):
        """Exits with error for a missing eval directory."""
        term = terminal(f"{SKILLET} eval /nonexistent/path/to/evals --trust")
        expect(term).to_have_exited()
        assert term.exit_code != 0
