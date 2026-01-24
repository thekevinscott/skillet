"""Frontmatter validation rule."""

from skillet.lint.types import LintFinding, LintSeverity, SkillDocument

from .base import LintRule

REQUIRED_FIELDS = ["name", "description"]


class FrontmatterValidRule(LintRule):
    """Checks for valid YAML frontmatter with required fields."""

    @property
    def rule_id(self) -> str:
        return "frontmatter-valid"

    @property
    def description(self) -> str:
        return "Checks for valid YAML frontmatter with required name and description fields"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        findings = []

        if doc.frontmatter is None:
            findings.append(
                LintFinding(
                    rule_id=self.rule_id,
                    message="Missing YAML frontmatter",
                    severity=LintSeverity.ERROR,
                    line=1,
                    suggestion="Add frontmatter with --- delimiters at the start of the file",
                )
            )
            return findings

        if not isinstance(doc.frontmatter, dict):
            findings.append(
                LintFinding(
                    rule_id=self.rule_id,
                    message="Frontmatter must be a YAML dictionary",
                    severity=LintSeverity.ERROR,
                    line=1,
                )
            )
            return findings

        for field in REQUIRED_FIELDS:
            if field not in doc.frontmatter:
                findings.append(
                    LintFinding(
                        rule_id=self.rule_id,
                        message=f"Missing required field: {field}",
                        severity=LintSeverity.ERROR,
                        line=1,
                        suggestion=f"Add '{field}: <value>' to the frontmatter",
                    )
                )
            elif not doc.frontmatter[field]:
                findings.append(
                    LintFinding(
                        rule_id=self.rule_id,
                        message=f"Field '{field}' is empty",
                        severity=LintSeverity.ERROR,
                        line=1,
                        suggestion=f"Provide a value for '{field}'",
                    )
                )

        return findings
