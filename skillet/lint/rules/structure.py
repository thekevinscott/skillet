"""Lint rules for skill file structure."""

from skillet.lint.rules.base import LintRule
from skillet.lint.types import LintFinding, LintSeverity, SkillDocument

MAX_DESCRIPTION_LENGTH = 1024
MAX_BODY_WORDS = 5000


def _extract_raw_frontmatter(content: str) -> str | None:
    """Extract the raw frontmatter text between --- delimiters."""
    if not content.startswith("---"):
        return None
    end_idx = content.find("\n---", 3)
    if end_idx == -1:
        return None
    return content[4:end_idx]


class FrontmatterDelimitersRule(LintRule):
    """Check that YAML frontmatter has --- delimiters."""

    name = "frontmatter-delimiters"
    description = "YAML frontmatter must have opening and closing --- delimiters"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        if not doc.content.startswith("---"):
            return [
                LintFinding(
                    rule=self.name,
                    message="Missing opening --- frontmatter delimiter",
                    severity=LintSeverity.ERROR,
                    line=1,
                )
            ]
        if doc.content.find("\n---", 3) == -1:
            return [
                LintFinding(
                    rule=self.name,
                    message="Missing closing --- frontmatter delimiter",
                    severity=LintSeverity.ERROR,
                    line=1,
                )
            ]
        return []


class FrontmatterNoXmlRule(LintRule):
    """Check that frontmatter contains no XML angle brackets."""

    name = "frontmatter-no-xml"
    description = "Frontmatter must not contain XML angle brackets (< >)"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        raw = _extract_raw_frontmatter(doc.content)
        if raw is None:
            return []
        if "<" in raw:
            return [
                LintFinding(
                    rule=self.name,
                    message="Frontmatter contains XML angle brackets (< >)",
                    severity=LintSeverity.ERROR,
                    line=1,
                )
            ]
        return []


class NoReadmeRule(LintRule):
    """Check that no README.md exists in the skill folder."""

    name = "no-readme"
    description = "Skill folder should not contain a README.md"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        readme = doc.path.parent / "README.md"
        if readme.exists():
            return [
                LintFinding(
                    rule=self.name,
                    message="Skill folder contains README.md (use SKILL.md instead)",
                    severity=LintSeverity.WARNING,
                )
            ]
        return []


class BodyWordCountRule(LintRule):
    """Check that the skill body is under 5,000 words."""

    name = "body-word-count"
    description = "Skill body should be under 5,000 words"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        word_count = len(doc.body.split())
        if word_count > MAX_BODY_WORDS:
            return [
                LintFinding(
                    rule=self.name,
                    message=f"Body has {word_count} words (recommended max: {MAX_BODY_WORDS})",
                    severity=LintSeverity.WARNING,
                )
            ]
        return []


class DescriptionLengthRule(LintRule):
    """Check that the description is under 1,024 characters."""

    name = "description-length"
    description = "Description should be under 1,024 characters"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        desc = doc.frontmatter.get("description")
        if not desc:
            return []
        if len(str(desc)) > MAX_DESCRIPTION_LENGTH:
            return [
                LintFinding(
                    rule=self.name,
                    message=(
                        f"Description is {len(str(desc))} chars (max: {MAX_DESCRIPTION_LENGTH})"
                    ),
                    severity=LintSeverity.WARNING,
                    line=1,
                )
            ]
        return []
