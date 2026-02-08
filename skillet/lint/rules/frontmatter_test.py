"""Tests for FrontmatterRule."""

from pathlib import Path

from skillet.lint.rules.frontmatter import FrontmatterRule
from skillet.lint.types import SkillDocument


def describe_frontmatter_rule():
    def it_passes_valid_frontmatter():
        doc = SkillDocument(
            path=Path("SKILL.md"),
            content="",
            frontmatter={"name": "my-skill", "description": "A skill."},
            body="",
        )

        findings = FrontmatterRule().check(doc)

        assert findings == []

    def it_warns_on_missing_name():
        doc = SkillDocument(
            path=Path("SKILL.md"),
            content="",
            frontmatter={"description": "A skill."},
            body="",
        )

        findings = FrontmatterRule().check(doc)

        assert len(findings) == 1
        assert findings[0].rule == "frontmatter-valid"
        assert "name" in findings[0].message

    def it_warns_on_missing_description():
        doc = SkillDocument(
            path=Path("SKILL.md"),
            content="",
            frontmatter={"name": "my-skill"},
            body="",
        )

        findings = FrontmatterRule().check(doc)

        assert len(findings) == 1
        assert "description" in findings[0].message

    def it_warns_on_both_missing():
        doc = SkillDocument(
            path=Path("SKILL.md"),
            content="",
            frontmatter={},
            body="",
        )

        findings = FrontmatterRule().check(doc)

        assert len(findings) == 2
