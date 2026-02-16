"""Tests for BodyWordCountRule."""

from pathlib import Path

from skillet.lint.rules.body_word_count import BodyWordCountRule
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


def describe_body_word_count_rule():
    def it_passes_for_short_body():
        assert BodyWordCountRule().check(_doc()) == []

    def it_warns_for_long_body():
        findings = BodyWordCountRule().check(_doc(body="word " * 5001))
        assert len(findings) == 1
        assert "5001" in findings[0].message

    def it_passes_at_exactly_5000():
        assert BodyWordCountRule().check(_doc(body="word " * 5000)) == []
