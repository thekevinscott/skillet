"""Lint rule for skill name matching its folder."""

from skillet.lint.rules.base import LintRule
from skillet.lint.types import LintFinding, LintSeverity, SkillDocument


class NameMatchesFolderRule(LintRule):
    """Check that the name field matches the parent folder name."""

    name = "name-matches-folder"
    description = "Name field must match the skill folder name"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        skill_name = doc.frontmatter.get("name", "")
        folder = doc.path.parent.name
        if skill_name and folder and skill_name != folder:
            return [
                LintFinding(
                    rule=self.name,
                    message=f"Name '{skill_name}' does not match folder '{folder}'",
                    severity=LintSeverity.WARNING,
                )
            ]
        return []
