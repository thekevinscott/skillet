"""Lint runner that orchestrates parsing and rule checking."""

from pathlib import Path

from skillet.errors import LintError
from skillet.lint.parse import parse_skill
from skillet.lint.rules import ALL_RULES
from skillet.lint.types import LintResult


def lint_skill(path: Path) -> LintResult:
    """Lint a SKILL.md file and return findings."""
    if not path.exists():
        raise LintError(f"File not found: {path}")

    doc = parse_skill(path)
    findings = []
    for rule in ALL_RULES:
        findings.extend(rule.check(doc))

    return LintResult(path=path, findings=findings)


async def lint_skill_async(path: Path) -> LintResult:
    """Lint a SKILL.md file with both static and LLM-assisted rules."""
    if not path.exists():
        raise LintError(f"File not found: {path}")

    from skillet.lint.rules import LLM_RULES

    doc = parse_skill(path)
    findings = []

    for rule in ALL_RULES:
        findings.extend(rule.check(doc))

    for rule in LLM_RULES:
        findings.extend(await rule.check_async(doc))

    return LintResult(path=path, findings=findings)
