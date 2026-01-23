"""Tests for section structure rule."""

from pathlib import Path

import pytest

from skillet.lint.rules.section_structure import RECOMMENDED_SECTIONS, SectionStructureRule
from skillet.lint.types import LintSeverity, SkillDocument


def make_doc(body: str) -> SkillDocument:
    """Create a SkillDocument with body content."""
    return SkillDocument(
        path=Path("/test/SKILL.md"),
        content=body,
        frontmatter={"name": "test", "description": "test"},
        body=body,
        line_count=len(body.splitlines()),
        frontmatter_end_line=4,
    )


def describe_section_structure_rule():
    """Tests for SectionStructureRule."""

    def it_passes_for_complete_structure():
        rule = SectionStructureRule()
        doc = make_doc(
            "# Role\nYou are helpful.\n\n"
            "# Goals\n- Help users\n\n"
            "# Instructions\nBe nice."
        )

        findings = rule.check(doc)

        assert len(findings) == 0

    def it_accepts_different_header_levels():
        rule = SectionStructureRule()
        doc = make_doc(
            "## Role\nYou are helpful.\n\n"
            "### Goals\n- Help users\n\n"
            "#### Instructions\nBe nice."
        )

        findings = rule.check(doc)

        assert len(findings) == 0

    def it_is_case_insensitive():
        rule = SectionStructureRule()
        doc = make_doc(
            "# ROLE\nYou are helpful.\n\n"
            "# goals\n- Help users\n\n"
            "# InStRuCtIoNs\nBe nice."
        )

        findings = rule.check(doc)

        assert len(findings) == 0

    @pytest.mark.parametrize("missing_section", RECOMMENDED_SECTIONS)
    def it_suggests_missing_sections(missing_section: str):
        rule = SectionStructureRule()
        sections = [s for s in RECOMMENDED_SECTIONS if s != missing_section]
        body = "\n".join([f"# {s}\nContent for {s}." for s in sections])
        doc = make_doc(body)

        findings = rule.check(doc)

        assert len(findings) == 1
        assert findings[0].severity == LintSeverity.SUGGESTION
        assert missing_section in findings[0].message

    def it_reports_all_missing_sections():
        rule = SectionStructureRule()
        doc = make_doc("# Overview\nJust some content.")

        findings = rule.check(doc)

        assert len(findings) == 3
        assert all(f.severity == LintSeverity.SUGGESTION for f in findings)
        messages = " ".join(f.message for f in findings)
        for section in RECOMMENDED_SECTIONS:
            assert section in messages

    def it_provides_suggestions():
        rule = SectionStructureRule()
        doc = make_doc("# Overview\nJust content.")

        findings = rule.check(doc)

        assert all(f.suggestion is not None for f in findings)
        assert all("##" in f.suggestion for f in findings)
