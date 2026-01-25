"""Tests for print_dry_run_output."""

from io import StringIO
from unittest.mock import patch

from rich.console import Console

from skillet.generate.types import CandidateEval

from .print_dry_run_output import print_dry_run_output


def _make_candidate(
    name: str = "test",
    prompt: str | list[str] = "Test prompt",
    expected: str = "Test expected",
) -> CandidateEval:
    return CandidateEval(
        prompt=prompt,
        expected=expected,
        name=name,
        category="positive",
        source="goal:1",
        confidence=0.9,
        rationale="Test rationale",
    )


def describe_print_dry_run_output():
    """Tests for print_dry_run_output function."""

    def it_shows_dry_run_message():
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)

        with patch(
            "skillet.cli.commands.generate_evals.print_dry_run_output.console",
            test_console,
        ):
            print_dry_run_output([])

        result = output.getvalue()
        assert "Dry run" in result
        assert "no files written" in result

    def it_shows_candidate_name_and_category():
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)
        candidates = [_make_candidate(name="my-eval")]

        with patch(
            "skillet.cli.commands.generate_evals.print_dry_run_output.console",
            test_console,
        ):
            print_dry_run_output(candidates)

        result = output.getvalue()
        assert "my-eval" in result
        assert "positive" in result

    def it_shows_prompt():
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)
        candidates = [_make_candidate(prompt="Do something specific")]

        with patch(
            "skillet.cli.commands.generate_evals.print_dry_run_output.console",
            test_console,
        ):
            print_dry_run_output(candidates)

        result = output.getvalue()
        assert "Prompt:" in result
        assert "Do something specific" in result

    def it_shows_expected():
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)
        candidates = [_make_candidate(expected="Expected outcome")]

        with patch(
            "skillet.cli.commands.generate_evals.print_dry_run_output.console",
            test_console,
        ):
            print_dry_run_output(candidates)

        result = output.getvalue()
        assert "Expected:" in result
        assert "Expected outcome" in result

    def it_truncates_long_prompts():
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)
        long_prompt = "a" * 200
        candidates = [_make_candidate(prompt=long_prompt)]

        with patch(
            "skillet.cli.commands.generate_evals.print_dry_run_output.console",
            test_console,
        ):
            print_dry_run_output(candidates)

        result = output.getvalue()
        assert "..." in result

    def it_handles_multi_turn_prompts():
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)
        candidates = [_make_candidate(prompt=["First turn", "Second turn"])]

        with patch(
            "skillet.cli.commands.generate_evals.print_dry_run_output.console",
            test_console,
        ):
            print_dry_run_output(candidates)

        result = output.getvalue()
        assert "First turn | Second turn" in result

    def it_handles_multiple_candidates():
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)
        candidates = [
            _make_candidate(name="first"),
            _make_candidate(name="second"),
        ]

        with patch(
            "skillet.cli.commands.generate_evals.print_dry_run_output.console",
            test_console,
        ):
            print_dry_run_output(candidates)

        result = output.getvalue()
        assert "first" in result
        assert "second" in result
