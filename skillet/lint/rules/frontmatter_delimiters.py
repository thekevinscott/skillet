"""Lint rule for YAML frontmatter delimiters."""

from skillet.lint.rules.base import LintRule
from skillet.lint.types import LintFinding, LintSeverity, SkillDocument


class FrontmatterDelimitersRule(LintRule):
    """Check that YAML frontmatter has --- delimiters."""

    name = "frontmatter-delimiters"
    description = "YAML frontmatter must have --- delimiters"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        lines = doc.content.splitlines()
        if not lines or lines[0].strip() != "---":
            return [
                LintFinding(
                    rule=self.name,
                    message="File must start with --- frontmatter delimiter",
                    severity=LintSeverity.ERROR,
                    line=1,
                )
            ]
        # Find closing delimiter
        for _i, line in enumerate(lines[1:], start=2):
            if line.strip() == "---":
                return []
        return [
            LintFinding(
                rule=self.name,
                message="Missing closing --- frontmatter delimiter",
                severity=LintSeverity.ERROR,
                line=1,
            )
        ]
