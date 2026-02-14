"""Tests for naming lint rules."""

from pathlib import Path

from skillet.lint.rules.naming import (
    FilenameCaseRule,
    FolderKebabCaseRule,
    NameKebabCaseRule,
)
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


def describe_folder_kebab_case_rule():
    def it_passes_for_kebab_case():
        assert FolderKebabCaseRule().check(_doc("my-skill/SKILL.md")) == []

    def it_warns_for_underscores():
        findings = FolderKebabCaseRule().check(_doc("my_skill/SKILL.md"))
        assert len(findings) == 1
        assert findings[0].rule == "folder-kebab-case"

    def it_warns_for_uppercase():
        findings = FolderKebabCaseRule().check(_doc("MySkill/SKILL.md"))
        assert len(findings) == 1

    def it_warns_for_spaces():
        findings = FolderKebabCaseRule().check(_doc("my skill/SKILL.md"))
        assert len(findings) == 1


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
