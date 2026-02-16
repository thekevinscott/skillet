"""Tests for FrontmatterDelimitersRule."""

from pathlib import Path

from skillet.lint.rules.frontmatter_delimiters import FrontmatterDelimitersRule
from skillet.lint.types import SkillDocument


def _doc(
    content: str = "---\nname: test\n---\nBody.",
    frontmatter: dict | None = None,
    body: str = "Some body text.",
    path: str = "my-skill/SKILL.md",
) -> SkillDocument:
    if frontmatter is None:
        frontmatter = {"name": "test", "description": "A skill."}
    return SkillDocument(path=Path(path), content=content, frontmatter=frontmatter, body=body)


def describe_frontmatter_delimiters_rule():
    def it_passes_with_valid_delimiters():
        assert FrontmatterDelimitersRule().check(_doc()) == []

    def it_errors_when_missing_opening():
        findings = FrontmatterDelimitersRule().check(_doc(content="name: test\n---\n"))
        assert len(findings) == 1
        assert findings[0].severity.value == "error"

    def it_errors_when_missing_closing():
        findings = FrontmatterDelimitersRule().check(_doc(content="---\nname: test\n"))
        assert len(findings) == 1
        assert "closing" in findings[0].message

    def it_errors_on_empty_content():
        findings = FrontmatterDelimitersRule().check(_doc(content=""))
        assert len(findings) == 1
