"""Tests for print_rules function."""

from .print_rules import print_rules


def describe_print_rules():
    """Tests for print_rules function."""

    def it_prints_all_rule_ids(capsys):
        print_rules()

        captured = capsys.readouterr()
        assert "frontmatter-valid" in captured.out

    def it_prints_rule_descriptions(capsys):
        print_rules()

        captured = capsys.readouterr()
        assert "frontmatter" in captured.out.lower()
