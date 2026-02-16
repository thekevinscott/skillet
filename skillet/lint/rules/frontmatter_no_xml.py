"""Lint rule for XML angle brackets in frontmatter."""

import re

from skillet.lint.rules.base import LintRule
from skillet.lint.types import LintFinding, LintSeverity, SkillDocument


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


def _extract_raw_frontmatter(content: str) -> str | None:
    """Extract raw frontmatter text between --- delimiters."""
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[1:i])
    return None
