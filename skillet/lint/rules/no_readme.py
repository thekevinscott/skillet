"""Lint rule for README.md in skill folders."""

from skillet.lint.rules.base import LintRule
from skillet.lint.types import LintFinding, LintSeverity, SkillDocument


class NoReadmeRule(LintRule):
    """Check that no README.md exists inside the skill folder."""

    name = "no-readme"
    description = "No README.md inside skill folder"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        readme = doc.path.parent / "README.md"
        if readme.exists():
            return [
                LintFinding(
                    rule=self.name,
                    message="Skill folder should not contain a README.md",
                    severity=LintSeverity.WARNING,
                )
            ]
        return []
