"""SKILL.md static linter.

Usage:
    from skillet.lint import lint

    result = lint(Path("skill/SKILL.md"))
    for finding in result.findings:
        print(f"{finding.severity}: {finding.message}")
"""

from .output import format_json, format_text
from .rules import ALL_RULES, RULES_BY_ID
from .runner import lint
from .types import LintFinding, LintResult, LintSeverity

__all__ = [
    "ALL_RULES",
    "RULES_BY_ID",
    "LintFinding",
    "LintResult",
    "LintSeverity",
    "format_json",
    "format_text",
    "lint",
]
