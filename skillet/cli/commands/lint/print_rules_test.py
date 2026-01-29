"""Tests for print_rules."""

from unittest.mock import patch

import pytest

from skillet.cli.commands.lint.print_rules import print_rules


def describe_print_rules():
    @pytest.fixture(autouse=True)
    def mock_console():
        with patch("skillet.cli.commands.lint.print_rules.console") as mock:
            yield mock

    def it_prints_rule_names(mock_console):
        print_rules()

        output = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "frontmatter-valid" in output
