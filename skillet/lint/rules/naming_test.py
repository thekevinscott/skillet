"""Tests for naming lint rules."""

from pathlib import Path

from skillet.lint.rules.naming import FilenameCaseRule
from skillet.lint.types import SkillDocument


def _doc(path: str = "SKILL.md") -> SkillDocument:
    return SkillDocument(
        path=Path(path),
        content="",
        frontmatter={"name": "test", "description": "A test skill."},
        body="",
    )


def describe_filename_case_rule():
    def it_passes_for_SKILL_md():
        assert FilenameCaseRule().check(_doc("SKILL.md")) == []

    def it_warns_for_lowercase():
        findings = FilenameCaseRule().check(_doc("skill.md"))
        assert len(findings) == 1
        assert findings[0].rule == "filename-case"

    def it_warns_for_mixed_case():
        findings = FilenameCaseRule().check(_doc("Skill.md"))
        assert len(findings) == 1
