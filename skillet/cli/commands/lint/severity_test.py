"""Tests for severity threshold checking."""

import pytest

from skillet.lint import LintSeverity

from .severity import severity_meets_threshold


def describe_severity_meets_threshold():
    """Tests for severity_meets_threshold function."""

    @pytest.mark.parametrize(
        ("severity", "threshold", "expected"),
        [
            # Error meets all thresholds
            (LintSeverity.ERROR, LintSeverity.ERROR, True),
            (LintSeverity.ERROR, LintSeverity.WARNING, True),
            (LintSeverity.ERROR, LintSeverity.SUGGESTION, True),
            # Warning meets warning and suggestion thresholds
            (LintSeverity.WARNING, LintSeverity.ERROR, False),
            (LintSeverity.WARNING, LintSeverity.WARNING, True),
            (LintSeverity.WARNING, LintSeverity.SUGGESTION, True),
            # Suggestion only meets suggestion threshold
            (LintSeverity.SUGGESTION, LintSeverity.ERROR, False),
            (LintSeverity.SUGGESTION, LintSeverity.WARNING, False),
            (LintSeverity.SUGGESTION, LintSeverity.SUGGESTION, True),
        ],
    )
    def it_correctly_compares_severities(
        severity: LintSeverity, threshold: LintSeverity, expected: bool
    ):
        assert severity_meets_threshold(severity, threshold) == expected
