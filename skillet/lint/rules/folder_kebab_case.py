"""Lint rule for skill folder kebab-case naming."""

import re

from skillet.lint.rules.base import LintRule
from skillet.lint.types import LintFinding, LintSeverity, SkillDocument

_KEBAB_CASE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class FolderKebabCaseRule(LintRule):
    """Check that the skill folder name is kebab-case."""

    name = "folder-kebab-case"
    description = "Skill folder name must be kebab-case"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        folder = doc.path.parent.name
        if not _KEBAB_CASE.match(folder):
            return [
                LintFinding(
                    rule=self.name,
                    message=f"Folder name must be kebab-case, got '{folder}'",
                    severity=LintSeverity.WARNING,
                )
            ]
        return []
