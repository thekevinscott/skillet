"""Tests for FrontmatterNoXmlRule."""

from pathlib import Path

from skillet.lint.rules.frontmatter_no_xml import FrontmatterNoXmlRule
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


def describe_frontmatter_no_xml_rule():
    def it_passes_with_clean_frontmatter():
        assert FrontmatterNoXmlRule().check(_doc()) == []

    def it_errors_with_angle_brackets():
        content = "---\ndescription: Use <tool> for work\n---\n"
        findings = FrontmatterNoXmlRule().check(_doc(content=content))
        assert len(findings) == 1
        assert findings[0].severity.value == "error"

    def it_ignores_angle_brackets_in_body():
        content = "---\nname: test\n---\nUse <tool> here."
        assert FrontmatterNoXmlRule().check(_doc(content=content)) == []

    def it_passes_when_no_frontmatter():
        assert FrontmatterNoXmlRule().check(_doc(content="no frontmatter")) == []
