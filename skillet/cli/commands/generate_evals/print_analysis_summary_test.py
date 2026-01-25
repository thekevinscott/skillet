"""Tests for print_analysis_summary."""

import re
from io import StringIO
from unittest.mock import patch

from rich.console import Console

from .print_analysis_summary import print_analysis_summary

# Module path for patching
_MODULE = "skillet.cli.commands.generate_evals.print_analysis_summary"

# Strip ANSI escape codes for assertions
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    return _ANSI_ESCAPE.sub("", text)


def describe_print_analysis_summary():
    """Tests for print_analysis_summary function."""

    def it_prints_skill_name():
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)

        with patch(f"{_MODULE}.console", test_console):
            print_analysis_summary({"name": "my-skill"})

        result = _strip_ansi(output.getvalue())
        assert "my-skill" in result

    def it_prints_unnamed_for_missing_name():
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)

        with patch(f"{_MODULE}.console", test_console):
            print_analysis_summary({})

        result = _strip_ansi(output.getvalue())
        assert "unnamed" in result

    def it_counts_goals():
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)

        with patch(f"{_MODULE}.console", test_console):
            print_analysis_summary({"goals": ["g1", "g2", "g3"]})

        result = _strip_ansi(output.getvalue())
        assert "Goals: 3" in result

    def it_counts_prohibitions():
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)

        with patch(f"{_MODULE}.console", test_console):
            print_analysis_summary({"prohibitions": ["p1", "p2"]})

        result = _strip_ansi(output.getvalue())
        assert "Prohibitions: 2" in result

    def it_shows_example_count():
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)

        with patch(f"{_MODULE}.console", test_console):
            print_analysis_summary({"example_count": 5})

        result = _strip_ansi(output.getvalue())
        assert "Examples: 5" in result

    def it_handles_empty_analysis():
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)

        with patch(f"{_MODULE}.console", test_console):
            print_analysis_summary({})

        result = _strip_ansi(output.getvalue())
        assert "Skill Analysis" in result
        assert "unnamed" in result
        assert "Goals: 0" in result
        assert "Prohibitions: 0" in result
        assert "Examples: 0" in result
