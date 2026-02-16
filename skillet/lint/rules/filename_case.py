"""Lint rule for skill filename casing."""

from skillet.lint.rules.base import LintRule
from skillet.lint.types import LintFinding, LintSeverity, SkillDocument


class FilenameCaseRule(LintRule):
    """Check that the skill file is named exactly SKILL.md."""

    name = "filename-case"
    description = "Skill file must be named exactly SKILL.md"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        if doc.path.name != "SKILL.md":
            return [
                LintFinding(
                    rule=self.name,
                    message=f"File should be named SKILL.md, got {doc.path.name}",
                    severity=LintSeverity.WARNING,
                )
            ]
        return []
