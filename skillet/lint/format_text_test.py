"""Tests for format_text function."""

from pathlib import Path

from .format_text import format_text
from .types import LintFinding, LintResult, LintSeverity


def describe_format_text():
    """Tests for format_text function."""

    def it_formats_empty_result():
        result = LintResult(path=Path("/test/SKILL.md"))

        output = format_text(result, use_color=False)

        assert "No issues found" in output

    def it_formats_single_finding():
        result = LintResult(
            path=Path("/test/SKILL.md"),
            findings=[
                LintFinding(
                    rule_id="test-rule",
                    message="Test message",
                    severity=LintSeverity.ERROR,
                    line=10,
                )
            ],
        )

        output = format_text(result, use_color=False)

        assert "/test/SKILL.md:10:1" in output
        assert "error[test-rule]" in output
        assert "Test message" in output
        assert "1 error" in output

    def it_formats_multiple_findings():
        result = LintResult(
            path=Path("/test/SKILL.md"),
            findings=[
                LintFinding(
                    rule_id="rule1",
                    message="Error",
                    severity=LintSeverity.ERROR,
                ),
                LintFinding(
                    rule_id="rule2",
                    message="Warning",
                    severity=LintSeverity.WARNING,
                ),
            ],
        )

        output = format_text(result, use_color=False)

        assert "1 error" in output
        assert "1 warning" in output

    def it_uses_color_codes_when_enabled():
        result = LintResult(
            path=Path("/test/SKILL.md"),
            findings=[
                LintFinding(
                    rule_id="test",
                    message="Error",
                    severity=LintSeverity.ERROR,
                )
            ],
        )

        output = format_text(result, use_color=True)

        assert "\033[31m" in output  # Red for error
