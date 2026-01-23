"""Lint runner that orchestrates rule execution."""

from pathlib import Path

from skillet.errors import LintError

from .parse import parse_skill
from .rules import ALL_RULES, RULES_BY_ID, LintRule
from .types import LintResult


def lint(
    path: Path,
    *,
    disabled_rules: list[str] | None = None,
) -> LintResult:
    """Lint a SKILL.md file and return findings.

    Args:
        path: Path to the SKILL.md file or directory containing SKILL.md
        disabled_rules: List of rule IDs to skip

    Returns:
        LintResult with all findings

    Raises:
        LintError: If the path doesn't exist or isn't a valid skill
        SkillParseError: If the SKILL.md file cannot be parsed
    """
    # Resolve to SKILL.md if directory
    if path.is_dir():
        skill_path = path / "SKILL.md"
        if not skill_path.exists():
            raise LintError(f"No SKILL.md found in {path}")
        path = skill_path
    elif not path.exists():
        raise LintError(f"Path does not exist: {path}")

    # Validate disabled rules
    disabled = set(disabled_rules or [])
    invalid_rules = disabled - set(RULES_BY_ID.keys())
    if invalid_rules:
        raise LintError(f"Unknown rule IDs: {', '.join(sorted(invalid_rules))}")

    # Select rules to run
    rules_to_run: list[LintRule] = [r for r in ALL_RULES if r.rule_id not in disabled]

    # Parse the skill document
    doc = parse_skill(path)

    # Run all rules and collect findings
    result = LintResult(path=path)
    for rule in rules_to_run:
        findings = rule.check(doc)
        result.findings.extend(findings)

    # Sort findings by line number (None sorts last)
    result.findings.sort(key=lambda f: (f.line is None, f.line or 0))

    return result
