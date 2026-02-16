"""Tests for FolderKebabCaseRule."""

from pathlib import Path

from skillet.lint.rules.folder_kebab_case import FolderKebabCaseRule
from skillet.lint.types import SkillDocument


def _doc(path: str = "my-skill/SKILL.md", name: str = "my-skill") -> SkillDocument:
    return SkillDocument(
        path=Path(path),
        content="",
        frontmatter={"name": name, "description": "A test skill."},
        body="",
    )


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
