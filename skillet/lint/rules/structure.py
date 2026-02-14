"""Lint rules for skill file structure."""

import re

from skillet.lint.rules.base import LintRule
from skillet.lint.types import LintFinding, LintSeverity, SkillDocument

_MAX_DESCRIPTION_LENGTH = 1024
_MAX_BODY_WORDS = 5000


class FrontmatterDelimitersRule(LintRule):
    """Check that YAML frontmatter has --- delimiters."""

    name = "frontmatter-delimiters"
    description = "YAML frontmatter must have --- delimiters"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        lines = doc.content.splitlines()
        if not lines or lines[0].strip() != "---":
            return [
                LintFinding(
                    rule=self.name,
                    message="File must start with --- frontmatter delimiter",
                    severity=LintSeverity.ERROR,
                    line=1,
                )
            ]
        # Find closing delimiter
        for _i, line in enumerate(lines[1:], start=2):
            if line.strip() == "---":
                return []
        return [
            LintFinding(
                rule=self.name,
                message="Missing closing --- frontmatter delimiter",
                severity=LintSeverity.ERROR,
                line=1,
            )
        ]


class FrontmatterNoXmlRule(LintRule):
    """Check that frontmatter contains no XML angle brackets."""

    name = "frontmatter-no-xml"
    description = "No XML angle brackets (< >) in frontmatter"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        raw = _extract_raw_frontmatter(doc.content)
        if raw and re.search(r"[<>]", raw):
            return [
                LintFinding(
                    rule=self.name,
                    message="Frontmatter must not contain XML angle brackets (< >)",
                    severity=LintSeverity.ERROR,
                )
            ]
        return []


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


class NoReadmeRule(LintRule):
    """Check that no README.md exists inside the skill folder."""

    name = "no-readme"
    description = "No README.md inside skill folder"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        readme = doc.path.parent / "README.md"
        if readme.exists():
            return [
                LintFinding(
                    rule=self.name,
                    message="Skill folder should not contain a README.md",
                    severity=LintSeverity.WARNING,
                )
            ]
        return []


def _extract_raw_frontmatter(content: str) -> str | None:
    """Extract raw frontmatter text between --- delimiters."""
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[1:i])
    return None
