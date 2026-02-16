"""Lint rule for body word count."""

from skillet.lint.rules.base import LintRule
from skillet.lint.types import LintFinding, LintSeverity, SkillDocument

_MAX_BODY_WORDS = 5000


class BodyWordCountRule(LintRule):
    """Check that SKILL.md body is under 5000 words."""

    name = "body-word-count"
    description = "Skill body should be under 5,000 words"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        word_count = len(doc.body.split())
        if word_count > _MAX_BODY_WORDS:
            return [
                LintFinding(
                    rule=self.name,
                    message=f"Body is {word_count} words (recommended max {_MAX_BODY_WORDS:,})",
                    severity=LintSeverity.WARNING,
                )
            ]
        return []
