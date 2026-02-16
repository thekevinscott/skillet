"""Tests for DescriptionLengthRule."""

from pathlib import Path

from skillet.lint.rules.description_length import DescriptionLengthRule
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


def describe_description_length_rule():
    def it_passes_for_short_description():
        assert DescriptionLengthRule().check(_doc()) == []

    def it_warns_for_long_description():
        fm = {"name": "test", "description": "x" * 1025}
        findings = DescriptionLengthRule().check(_doc(frontmatter=fm))
        assert len(findings) == 1
        assert "1025" in findings[0].message

    def it_passes_at_exactly_1024():
        fm = {"name": "test", "description": "x" * 1024}
        assert DescriptionLengthRule().check(_doc(frontmatter=fm)) == []
