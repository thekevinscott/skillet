"""Severity threshold checking."""

from skillet.lint import LintSeverity

# Severity ranking: higher = more severe
SEVERITY_ORDER = {
    LintSeverity.ERROR: 3,
    LintSeverity.WARNING: 2,
    LintSeverity.SUGGESTION: 1,
}


def severity_meets_threshold(severity: LintSeverity, threshold: LintSeverity) -> bool:
    """Check if a severity meets or exceeds the threshold.

    Args:
        severity: The severity to check
        threshold: The minimum severity threshold

    Returns:
        True if severity >= threshold (ERROR > WARNING > SUGGESTION)
    """
    return SEVERITY_ORDER[severity] >= SEVERITY_ORDER[threshold]
