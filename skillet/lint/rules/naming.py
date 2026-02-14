"""Lint rules for skill naming conventions."""

import re

from skillet.lint.rules.base import LintRule
from skillet.lint.types import LintFinding, LintSeverity, SkillDocument

KEBAB_CASE_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
RESERVED_WORDS = {"claude", "anthropic"}


class FilenameCaseRule(LintRule):
    """Check that the skill file is named exactly SKILL.md."""

    name = "filename-case"
    description = "Skill file must be named SKILL.md (exact case)"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        if doc.path.name != "SKILL.md":
            return [
                LintFinding(
                    rule=self.name,
                    message=f"Expected filename SKILL.md, got {doc.path.name}",
                    severity=LintSeverity.WARNING,
                )
            ]
        return []


class FolderKebabCaseRule(LintRule):
    """Check that the skill folder name is kebab-case."""

    name = "folder-kebab-case"
    description = "Skill folder name must be kebab-case (lowercase, hyphens only)"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        folder = doc.path.parent.name
        if not KEBAB_CASE_RE.match(folder):
            return [
                LintFinding(
                    rule=self.name,
                    message=f"Folder name '{folder}' is not kebab-case",
                    severity=LintSeverity.WARNING,
                )
            ]
        return []


class NameKebabCaseRule(LintRule):
    """Check that the name field is kebab-case."""

    name = "name-kebab-case"
    description = "Name field must be kebab-case (lowercase, hyphens only)"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        skill_name = doc.frontmatter.get("name")
        if not skill_name:
            return []
        if not KEBAB_CASE_RE.match(skill_name):
            return [
                LintFinding(
                    rule=self.name,
                    message=f"Name '{skill_name}' is not kebab-case",
                    severity=LintSeverity.WARNING,
                    line=1,
                )
            ]
        return []


class NameMatchesFolderRule(LintRule):
    """Check that the name field matches the parent folder name."""

    name = "name-matches-folder"
    description = "Name field must match the skill folder name"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        skill_name = doc.frontmatter.get("name")
        if not skill_name:
            return []
        folder = doc.path.parent.name
        if skill_name != folder:
            return [
                LintFinding(
                    rule=self.name,
                    message=f"Name '{skill_name}' does not match folder '{folder}'",
                    severity=LintSeverity.WARNING,
                    line=1,
                )
            ]
        return []


class NameNoReservedRule(LintRule):
    """Check that the name does not contain reserved words."""

    name = "name-no-reserved"
    description = "Name must not contain 'claude' or 'anthropic' (reserved)"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        skill_name = doc.frontmatter.get("name")
        if not skill_name:
            return []
        name_lower = skill_name.lower()
        for word in RESERVED_WORDS:
            if word in name_lower:
                return [
                    LintFinding(
                        rule=self.name,
                        message=f"Name '{skill_name}' contains reserved word '{word}'",
                        severity=LintSeverity.ERROR,
                        line=1,
                    )
                ]
        return []
