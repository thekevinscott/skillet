"""Tests for NameKebabCaseRule."""

from pathlib import Path

from skillet.lint.rules.name_kebab_case import NameKebabCaseRule
from skillet.lint.types import SkillDocument


def _doc(path: str = "my-skill/SKILL.md", name: str = "my-skill") -> SkillDocument:
    return SkillDocument(
        path=Path(path),
        content="",
        frontmatter={"name": name, "description": "A test skill."},
        body="",
    )


def describe_name_kebab_case_rule():
    def it_passes_for_kebab_case():
        assert NameKebabCaseRule().check(_doc(name="my-skill")) == []

    def it_warns_for_underscores():
        findings = NameKebabCaseRule().check(_doc(name="my_skill"))
        assert len(findings) == 1
        assert findings[0].rule == "name-kebab-case"

    def it_warns_for_uppercase():
        findings = NameKebabCaseRule().check(_doc(name="MySkill"))
        assert len(findings) == 1

    def it_skips_when_name_missing():
        assert NameKebabCaseRule().check(_doc(name="")) == []
