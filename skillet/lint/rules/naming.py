"""Lint rules for skill naming conventions."""

import re

from skillet.lint.rules.base import LintRule
from skillet.lint.types import LintFinding, LintSeverity, SkillDocument

_KEBAB_CASE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


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
