"""Tests for NameNoReservedRule."""

from pathlib import Path

from skillet.lint.rules.name_no_reserved import NameNoReservedRule
from skillet.lint.types import SkillDocument


def _doc(path: str = "my-skill/SKILL.md", name: str = "my-skill") -> SkillDocument:
    return SkillDocument(
        path=Path(path),
        content="",
        frontmatter={"name": name, "description": "A test skill."},
        body="",
    )


def describe_name_no_reserved_rule():
    def it_passes_for_normal_name():
        assert NameNoReservedRule().check(_doc(name="my-skill")) == []

    def it_errors_for_claude_in_name():
        findings = NameNoReservedRule().check(_doc(name="claude-helper"))
        assert len(findings) == 1
        assert findings[0].rule == "name-no-reserved"
        assert findings[0].severity.value == "error"

    def it_errors_for_anthropic_in_name():
        findings = NameNoReservedRule().check(_doc(name="anthropic-tools"))
        assert len(findings) == 1

    def it_is_case_insensitive():
        findings = NameNoReservedRule().check(_doc(name="Claude-Helper"))
        assert len(findings) == 1
