"""Lint rule: validate SKILL.md frontmatter fields."""

from skillet.lint.rules.base import LintRule
from skillet.lint.types import LintFinding, LintSeverity, SkillDocument

REQUIRED_FIELDS = ["name", "description"]


class FrontmatterRule(LintRule):
    """Check that frontmatter contains required fields."""

    name = "frontmatter-valid"
    description = "Frontmatter must include name and description"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        findings = []
        for field in REQUIRED_FIELDS:
            if not doc.frontmatter.get(field):
                findings.append(
                    LintFinding(
                        rule=self.name,
                        message=f"Frontmatter missing required field: {field}",
                        severity=LintSeverity.WARNING,
                        line=1,
                    )
                )
        return findings
