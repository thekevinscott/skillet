"""Lint rule for description length."""

from skillet.lint.rules.base import LintRule
from skillet.lint.types import LintFinding, LintSeverity, SkillDocument

_MAX_DESCRIPTION_LENGTH = 1024


class DescriptionLengthRule(LintRule):
    """Check that description is under 1024 characters."""

    name = "description-length"
    description = "Description must be under 1024 characters"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        desc = doc.frontmatter.get("description", "")
        if len(desc) > _MAX_DESCRIPTION_LENGTH:
            return [
                LintFinding(
                    rule=self.name,
                    message=f"Description is {len(desc)} chars (max {_MAX_DESCRIPTION_LENGTH})",
                    severity=LintSeverity.WARNING,
                )
            ]
        return []
