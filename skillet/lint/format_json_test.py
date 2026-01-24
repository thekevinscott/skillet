"""Tests for format_json function."""

import json
from pathlib import Path

from .format_json import format_json
from .types import LintFinding, LintResult, LintSeverity


def describe_format_json():
    """Tests for format_json function."""

    def it_returns_valid_json():
        result = LintResult(path=Path("/test/SKILL.md"))

        output = format_json(result)
        data = json.loads(output)

        assert "path" in data
        assert "findings" in data
        assert "summary" in data

    def it_includes_finding_details():
        result = LintResult(
            path=Path("/test/SKILL.md"),
            findings=[
                LintFinding(
                    rule_id="test-rule",
                    message="Test message",
                    severity=LintSeverity.ERROR,
                    line=10,
                    suggestion="Fix it",
                )
            ],
        )

        output = format_json(result)
        data = json.loads(output)

        assert len(data["findings"]) == 1
        finding = data["findings"][0]
        assert finding["rule_id"] == "test-rule"
        assert finding["message"] == "Test message"
        assert finding["severity"] == "error"
        assert finding["line"] == 10
        assert finding["suggestion"] == "Fix it"

    def it_includes_summary_counts():
        result = LintResult(
            path=Path("/test/SKILL.md"),
            findings=[
                LintFinding(rule_id="r1", message="e", severity=LintSeverity.ERROR),
                LintFinding(rule_id="r2", message="w", severity=LintSeverity.WARNING),
            ],
        )

        output = format_json(result)
        data = json.loads(output)

        assert data["summary"]["errors"] == 1
        assert data["summary"]["warnings"] == 1
        assert data["summary"]["total"] == 2
