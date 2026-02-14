"""Lint rules for skill naming conventions."""

import re

from skillet.lint.rules.base import LintRule
from skillet.lint.types import LintFinding, LintSeverity, SkillDocument

_KEBAB_CASE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_RESERVED_NAMES = {"claude", "anthropic"}


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
