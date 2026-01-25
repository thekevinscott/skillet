"""Tests for print_candidates_table."""

from io import StringIO
from unittest.mock import patch

from rich.console import Console

from skillet.generate.types import CandidateEval

from .print_candidates_table import print_candidates_table


def _make_candidate(
    name: str = "test",
    category: str = "positive",
    source: str = "goal:1",
    confidence: float = 0.9,
) -> CandidateEval:
    return CandidateEval(
        prompt="Test prompt",
        expected="Test expected",
        name=name,
        category=category,
        source=source,
        confidence=confidence,
        rationale="Test rationale",
    )


def describe_print_candidates_table():
    """Tests for print_candidates_table function."""

    def it_prints_no_candidates_message_when_empty():
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)

        with patch(
            "skillet.cli.commands.generate_evals.print_candidates_table.console",
            test_console,
        ):
            print_candidates_table([])

        result = output.getvalue()
        assert "No candidates generated" in result

    def it_prints_table_with_candidates():
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)
        candidates = [_make_candidate(name="test-eval")]

        with patch(
            "skillet.cli.commands.generate_evals.print_candidates_table.console",
            test_console,
        ):
            print_candidates_table(candidates)

        result = output.getvalue()
        assert "test-eval" in result
        assert "Generated Candidates (1)" in result

    def it_shows_candidate_category():
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)
        candidates = [_make_candidate(category="negative")]

        with patch(
            "skillet.cli.commands.generate_evals.print_candidates_table.console",
            test_console,
        ):
            print_candidates_table(candidates)

        result = output.getvalue()
        assert "negative" in result

    def it_shows_candidate_source():
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)
        candidates = [_make_candidate(source="lint:vague-language")]

        with patch(
            "skillet.cli.commands.generate_evals.print_candidates_table.console",
            test_console,
        ):
            print_candidates_table(candidates)

        result = output.getvalue()
        assert "lint:vague-language" in result

    def it_shows_confidence_percentage():
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)
        candidates = [_make_candidate(confidence=0.85)]

        with patch(
            "skillet.cli.commands.generate_evals.print_candidates_table.console",
            test_console,
        ):
            print_candidates_table(candidates)

        result = output.getvalue()
        assert "85%" in result

    def it_handles_multiple_candidates():
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)
        candidates = [
            _make_candidate(name="first"),
            _make_candidate(name="second"),
            _make_candidate(name="third"),
        ]

        with patch(
            "skillet.cli.commands.generate_evals.print_candidates_table.console",
            test_console,
        ):
            print_candidates_table(candidates)

        result = output.getvalue()
        assert "Generated Candidates (3)" in result
        assert "first" in result
        assert "second" in result
        assert "third" in result
