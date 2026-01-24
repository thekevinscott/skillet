"""Tests for frontmatter validation rule."""

from pathlib import Path

import pytest

from skillet.lint.types import LintSeverity, SkillDocument

from .frontmatter import FrontmatterValidRule


def make_doc(frontmatter: dict | None) -> SkillDocument:
    """Create a SkillDocument with given frontmatter."""
    return SkillDocument(
        path=Path("/test/SKILL.md"),
        content="",
        frontmatter=frontmatter,
        body="",
        line_count=1,
        frontmatter_end_line=4 if frontmatter else 0,
    )


def describe_frontmatter_valid_rule():
    """Tests for FrontmatterValidRule."""

    def it_passes_for_valid_frontmatter():
        rule = FrontmatterValidRule()
        doc = make_doc({"name": "test-skill", "description": "A test skill"})

        findings = rule.check(doc)

        assert len(findings) == 0

    def it_errors_on_missing_frontmatter():
        rule = FrontmatterValidRule()
        doc = make_doc(None)

        findings = rule.check(doc)

        assert len(findings) == 1
        assert findings[0].severity == LintSeverity.ERROR
        assert "Missing" in findings[0].message

    def it_errors_on_missing_name():
        rule = FrontmatterValidRule()
        doc = make_doc({"description": "A test skill"})

        findings = rule.check(doc)

        assert len(findings) == 1
        assert "name" in findings[0].message

    def it_errors_on_missing_description():
        rule = FrontmatterValidRule()
        doc = make_doc({"name": "test-skill"})

        findings = rule.check(doc)

        assert len(findings) == 1
        assert "description" in findings[0].message

    def it_errors_on_empty_name():
        rule = FrontmatterValidRule()
        doc = make_doc({"name": "", "description": "A test skill"})

        findings = rule.check(doc)

        assert len(findings) == 1
        assert "empty" in findings[0].message.lower()

    def it_errors_on_non_dict_frontmatter():
        rule = FrontmatterValidRule()
        doc = make_doc("not a dict")  # type: ignore[arg-type]

        findings = rule.check(doc)

        assert len(findings) == 1
        assert "dictionary" in findings[0].message.lower()

    @pytest.mark.parametrize(
        "missing_fields",
        [
            {"name": "test"},  # missing description
            {"description": "test"},  # missing name
            {},  # missing both
        ],
    )
    def it_reports_all_missing_fields(missing_fields: dict):
        rule = FrontmatterValidRule()
        doc = make_doc(missing_fields)

        findings = rule.check(doc)

        expected_count = 2 - len(missing_fields)
        assert len(findings) == expected_count
