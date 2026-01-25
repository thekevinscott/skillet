"""Tests for print_output_summary."""

from io import StringIO
from pathlib import Path
from unittest.mock import patch

from rich.console import Console

from skillet.generate.types import CandidateEval

from .print_output_summary import print_output_summary


def _make_candidate(name: str = "test", category: str = "positive") -> CandidateEval:
    return CandidateEval(
        prompt="Test prompt",
        expected="Test expected",
        name=name,
        category=category,
        source="goal:1",
        confidence=0.9,
        rationale="Test rationale",
    )


def describe_print_output_summary():
    """Tests for print_output_summary function."""

    def it_shows_output_directory():
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)

        with patch(
            "skillet.cli.commands.generate_evals.print_output_summary.console",
            test_console,
        ):
            print_output_summary([], Path("/my/output"))

        result = output.getvalue()
        assert "/my/output" in result
        assert "Generated" in result

    def it_lists_candidate_files():
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)
        candidates = [_make_candidate(name="test-eval")]

        with patch(
            "skillet.cli.commands.generate_evals.print_output_summary.console",
            test_console,
        ):
            print_output_summary(candidates, Path("/output"))

        result = output.getvalue()
        assert "test-eval.yaml" in result

    def it_shows_category_for_each_file():
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)
        candidates = [_make_candidate(name="neg-eval", category="negative")]

        with patch(
            "skillet.cli.commands.generate_evals.print_output_summary.console",
            test_console,
        ):
            print_output_summary(candidates, Path("/output"))

        result = output.getvalue()
        assert "negative" in result

    def it_shows_next_steps():
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)

        with patch(
            "skillet.cli.commands.generate_evals.print_output_summary.console",
            test_console,
        ):
            print_output_summary([], Path("/output"))

        result = output.getvalue()
        assert "Next steps:" in result
        assert "Review candidates" in result
        assert "Edit prompts" in result
        assert "_meta comments" in result
        assert "eval directory" in result

    def it_handles_multiple_candidates():
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)
        candidates = [
            _make_candidate(name="first"),
            _make_candidate(name="second"),
            _make_candidate(name="third"),
        ]

        with patch(
            "skillet.cli.commands.generate_evals.print_output_summary.console",
            test_console,
        ):
            print_output_summary(candidates, Path("/output"))

        result = output.getvalue()
        assert "first.yaml" in result
        assert "second.yaml" in result
        assert "third.yaml" in result
