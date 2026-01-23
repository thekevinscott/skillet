"""Tests for passive voice rule."""

from pathlib import Path

import pytest

from skillet.lint.rules.passive_voice import PassiveVoiceRule
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


def describe_passive_voice_rule():
    """Tests for PassiveVoiceRule."""

    def it_passes_for_active_voice():
        rule = PassiveVoiceRule()
        doc = make_doc("Handle errors with specific messages.")

        findings = rule.check(doc)

        assert len(findings) == 0

    @pytest.mark.parametrize(
        "passive_phrase",
        [
            "should be handled",
            "must be processed",
            "can be validated",
            "will be returned",
            "is computed",
            "are generated",
            "was deleted",
            "were updated",
        ],
    )
    def it_detects_passive_constructions(passive_phrase: str):
        rule = PassiveVoiceRule()
        doc = make_doc(f"Errors {passive_phrase} by the system.")

        findings = rule.check(doc)

        assert len(findings) >= 1
        assert all(f.severity == LintSeverity.WARNING for f in findings)

    def it_reports_line_numbers():
        rule = PassiveVoiceRule()
        doc = make_doc("Line one.\nData should be processed.\nLine three.")

        findings = rule.check(doc)

        assert len(findings) >= 1
        assert findings[0].line == 6  # 4 frontmatter + 2nd body line

    def it_ignores_common_false_positives():
        rule = PassiveVoiceRule()
        doc = make_doc(
            "The function is expected to return a value.\n"
            "This API is used for authentication.\n"
            "The method is called automatically.\n"
            "Variables are named descriptively.\n"
            "Types are defined in the schema."
        )

        findings = rule.check(doc)

        # Should not flag these common patterns
        assert len(findings) == 0

    def it_provides_suggestions():
        rule = PassiveVoiceRule()
        doc = make_doc("Data should be validated.")

        findings = rule.check(doc)

        assert len(findings) >= 1
        assert findings[0].suggestion is not None
        assert "active" in findings[0].suggestion.lower()

    def it_ignores_frontmatter():
        rule = PassiveVoiceRule()
        doc = SkillDocument(
            path=Path("/test/SKILL.md"),
            content="---\nname: should-be-fine\ndescription: test\n---\nClean body.",
            frontmatter={"name": "should-be-fine", "description": "test"},
            body="Clean body.",
            line_count=5,
            frontmatter_end_line=4,
        )

        findings = rule.check(doc)

        assert len(findings) == 0
