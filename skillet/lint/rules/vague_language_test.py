"""Tests for vague language rule."""

from pathlib import Path

import pytest

from skillet.lint.rules.vague_language import VagueLanguageRule
from skillet.lint.types import LintSeverity, SkillDocument


def make_doc(body: str, frontmatter_end_line: int = 4) -> SkillDocument:
    """Create a SkillDocument with body content."""
    frontmatter = "---\nname: test\ndescription: test\n---\n"
    content = frontmatter + body
    return SkillDocument(
        path=Path("/test/SKILL.md"),
        content=content,
        frontmatter={"name": "test", "description": "test"},
        body=body,
        line_count=len(content.splitlines()),
        frontmatter_end_line=frontmatter_end_line,
    )


def describe_vague_language_rule():
    """Tests for VagueLanguageRule."""

    def it_passes_for_precise_language():
        rule = VagueLanguageRule()
        doc = make_doc("Use specific error messages with error codes.")

        findings = rule.check(doc)

        assert len(findings) == 0

    @pytest.mark.parametrize(
        "vague_term",
        [
            "properly",
            "correctly",
            "appropriately",
            "as needed",
            "as required",
            "as necessary",
            "etc",
            "and so on",
            "and more",
            "if applicable",
            "when possible",
            "as appropriate",
        ],
    )
    def it_detects_vague_terms(vague_term: str):
        rule = VagueLanguageRule()
        doc = make_doc(f"Handle errors {vague_term}.")

        findings = rule.check(doc)

        assert len(findings) >= 1
        assert any(vague_term in f.message for f in findings)
        assert all(f.severity == LintSeverity.WARNING for f in findings)

    def it_reports_line_numbers():
        rule = VagueLanguageRule()
        doc = make_doc("Line one.\nHandle errors properly.\nLine three.")

        findings = rule.check(doc)

        assert len(findings) == 1
        # Line 5 = 4 frontmatter lines + 2nd body line
        assert findings[0].line == 6

    def it_detects_multiple_issues_on_same_line():
        rule = VagueLanguageRule()
        doc = make_doc("Handle errors properly and correctly.")

        findings = rule.check(doc)

        assert len(findings) == 2
        messages = [f.message for f in findings]
        assert any("properly" in m for m in messages)
        assert any("correctly" in m for m in messages)

    def it_ignores_frontmatter_lines():
        rule = VagueLanguageRule()
        # Put "properly" in what would be frontmatter area
        doc = SkillDocument(
            path=Path("/test/SKILL.md"),
            content="---\nname: properly-named\ndescription: test\n---\nClean body.",
            frontmatter={"name": "properly-named", "description": "test"},
            body="Clean body.",
            line_count=5,
            frontmatter_end_line=4,
        )

        findings = rule.check(doc)

        assert len(findings) == 0

    def it_provides_suggestions():
        rule = VagueLanguageRule()
        doc = make_doc("Do things properly.")

        findings = rule.check(doc)

        assert len(findings) == 1
        assert findings[0].suggestion is not None
        assert len(findings[0].suggestion) > 0

    def it_uses_word_boundaries():
        rule = VagueLanguageRule()
        # "property" contains "proper" but shouldn't match
        doc = make_doc("Set the property value.")

        findings = rule.check(doc)

        assert len(findings) == 0
