"""Tests for size limit rule."""

from pathlib import Path

import pytest

from skillet.lint.rules.size_limit import ERROR_THRESHOLD, WARNING_THRESHOLD, SizeLimitRule
from skillet.lint.types import LintSeverity, SkillDocument


def make_doc(line_count: int) -> SkillDocument:
    """Create a SkillDocument with specified line count."""
    content = "\n".join([f"line {i}" for i in range(line_count)])
    return SkillDocument(
        path=Path("/test/SKILL.md"),
        content=content,
        frontmatter={"name": "test", "description": "test"},
        body=content,
        line_count=line_count,
        frontmatter_end_line=3,
    )


def describe_size_limit_rule():
    """Tests for SizeLimitRule."""

    def it_passes_for_small_files():
        rule = SizeLimitRule()
        doc = make_doc(100)

        findings = rule.check(doc)

        assert len(findings) == 0

    def it_passes_just_below_warning_threshold():
        rule = SizeLimitRule()
        doc = make_doc(WARNING_THRESHOLD - 1)

        findings = rule.check(doc)

        assert len(findings) == 0

    def it_warns_at_warning_threshold():
        rule = SizeLimitRule()
        doc = make_doc(WARNING_THRESHOLD)

        findings = rule.check(doc)

        assert len(findings) == 1
        assert findings[0].severity == LintSeverity.WARNING
        assert str(WARNING_THRESHOLD) in findings[0].message

    def it_warns_between_thresholds():
        rule = SizeLimitRule()
        doc = make_doc(450)

        findings = rule.check(doc)

        assert len(findings) == 1
        assert findings[0].severity == LintSeverity.WARNING

    def it_errors_at_error_threshold():
        rule = SizeLimitRule()
        doc = make_doc(ERROR_THRESHOLD)

        findings = rule.check(doc)

        assert len(findings) == 1
        assert findings[0].severity == LintSeverity.ERROR
        assert str(ERROR_THRESHOLD) in findings[0].message

    def it_errors_above_error_threshold():
        rule = SizeLimitRule()
        doc = make_doc(1000)

        findings = rule.check(doc)

        assert len(findings) == 1
        assert findings[0].severity == LintSeverity.ERROR

    @pytest.mark.parametrize(
        "line_count,expected_severity",
        [
            (100, None),
            (399, None),
            (400, LintSeverity.WARNING),
            (450, LintSeverity.WARNING),
            (499, LintSeverity.WARNING),
            (500, LintSeverity.ERROR),
            (1000, LintSeverity.ERROR),
        ],
    )
    def it_uses_correct_severity_for_line_counts(
        line_count: int, expected_severity: LintSeverity | None
    ):
        rule = SizeLimitRule()
        doc = make_doc(line_count)

        findings = rule.check(doc)

        if expected_severity is None:
            assert len(findings) == 0
        else:
            assert len(findings) == 1
            assert findings[0].severity == expected_severity
