"""Tests for FilenameCaseRule."""

from pathlib import Path

from skillet.lint.rules.filename_case import FilenameCaseRule
from skillet.lint.types import SkillDocument


def _doc(path: str = "my-skill/SKILL.md", name: str = "my-skill") -> SkillDocument:
    return SkillDocument(
        path=Path(path),
        content="",
        frontmatter={"name": name, "description": "A test skill."},
        body="",
    )


def describe_filename_case_rule():
    def it_passes_for_SKILL_md():
        assert FilenameCaseRule().check(_doc()) == []

    def it_warns_for_lowercase():
        findings = FilenameCaseRule().check(_doc("my-skill/skill.md"))
        assert len(findings) == 1
        assert findings[0].rule == "filename-case"

    def it_warns_for_mixed_case():
        findings = FilenameCaseRule().check(_doc("my-skill/Skill.md"))
        assert len(findings) == 1
