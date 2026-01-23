"""Tests for frontmatter validation rule."""

from pathlib import Path

import pytest

from skillet.lint.rules.frontmatter import FrontmatterValidRule
from skillet.lint.types import LintSeverity, SkillDocument


def make_doc(
    content: str,
    frontmatter: dict | None = None,
    frontmatter_end_line: int = 0,
) -> SkillDocument:
    """Create a SkillDocument for testing."""
    return SkillDocument(
        path=Path("/test/SKILL.md"),
        content=content,
        frontmatter=frontmatter,
        body=content,
        line_count=len(content.splitlines()),
        frontmatter_end_line=frontmatter_end_line,
    )


def describe_frontmatter_valid_rule():
    """Tests for FrontmatterValidRule."""

    def it_passes_for_valid_frontmatter():
        rule = FrontmatterValidRule()
        doc = make_doc(
            "content",
            frontmatter={"name": "test", "description": "A test skill"},
            frontmatter_end_line=4,
        )

        findings = rule.check(doc)

        assert len(findings) == 0

    def it_errors_on_missing_frontmatter():
        rule = FrontmatterValidRule()
        doc = make_doc("No frontmatter here", frontmatter=None)

        findings = rule.check(doc)

        assert len(findings) == 1
        assert findings[0].severity == LintSeverity.ERROR
        assert "frontmatter" in findings[0].message.lower()

    def it_errors_on_missing_name():
        rule = FrontmatterValidRule()
        doc = make_doc(
            "content",
            frontmatter={"description": "A skill"},
            frontmatter_end_line=3,
        )

        findings = rule.check(doc)

        assert len(findings) == 1
        assert findings[0].severity == LintSeverity.ERROR
        assert "name" in findings[0].message

    def it_errors_on_missing_description():
        rule = FrontmatterValidRule()
        doc = make_doc(
            "content",
            frontmatter={"name": "test"},
            frontmatter_end_line=3,
        )

        findings = rule.check(doc)

        assert len(findings) == 1
        assert findings[0].severity == LintSeverity.ERROR
        assert "description" in findings[0].message

    def it_errors_on_empty_name():
        rule = FrontmatterValidRule()
        doc = make_doc(
            "content",
            frontmatter={"name": "", "description": "A skill"},
            frontmatter_end_line=4,
        )

        findings = rule.check(doc)

        assert len(findings) == 1
        assert findings[0].severity == LintSeverity.ERROR
        assert "empty" in findings[0].message.lower()
        assert "name" in findings[0].message

    def it_errors_on_non_dict_frontmatter():
        rule = FrontmatterValidRule()
        doc = make_doc(
            "content",
            frontmatter="just a string",  # type: ignore[arg-type]
            frontmatter_end_line=3,
        )

        findings = rule.check(doc)

        assert len(findings) == 1
        assert findings[0].severity == LintSeverity.ERROR
        assert "mapping" in findings[0].message.lower()

    @pytest.mark.parametrize(
        "missing_fields",
        [
            ["name"],
            ["description"],
            ["name", "description"],
        ],
    )
    def it_reports_all_missing_fields(missing_fields: list[str]):
        rule = FrontmatterValidRule()
        frontmatter = {"name": "test", "description": "desc"}
        for field in missing_fields:
            del frontmatter[field]

        doc = make_doc("content", frontmatter=frontmatter, frontmatter_end_line=3)

        findings = rule.check(doc)

        assert len(findings) == len(missing_fields)
        for field in missing_fields:
            assert any(field in f.message for f in findings)
