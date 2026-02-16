"""Lint rule for reserved words in skill names."""

from skillet.lint.rules.base import LintRule
from skillet.lint.types import LintFinding, LintSeverity, SkillDocument

_RESERVED_NAMES = {"claude", "anthropic"}


class NameNoReservedRule(LintRule):
    """Check that the skill name doesn't contain reserved words."""

    name = "name-no-reserved"
    description = "Name must not contain 'claude' or 'anthropic'"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        skill_name = doc.frontmatter.get("name", "").lower()
        for word in _RESERVED_NAMES:
            if word in skill_name:
                return [
                    LintFinding(
                        rule=self.name,
                        message=f"Name must not contain reserved word '{word}'",
                        severity=LintSeverity.ERROR,
                    )
                ]
        return []
