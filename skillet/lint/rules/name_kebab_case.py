"""Lint rule for skill name kebab-case formatting."""

import re

from skillet.lint.rules.base import LintRule
from skillet.lint.types import LintFinding, LintSeverity, SkillDocument

_KEBAB_CASE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class NameKebabCaseRule(LintRule):
    """Check that the name frontmatter field is kebab-case."""

    name = "name-kebab-case"
    description = "Name field must be kebab-case"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        skill_name = doc.frontmatter.get("name", "")
        if skill_name and not _KEBAB_CASE.match(skill_name):
            return [
                LintFinding(
                    rule=self.name,
                    message=f"Name must be kebab-case, got '{skill_name}'",
                    severity=LintSeverity.WARNING,
                )
            ]
        return []
