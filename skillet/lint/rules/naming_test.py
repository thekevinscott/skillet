"""Tests for naming lint rules."""

from pathlib import Path

import pytest

from skillet.lint.rules.naming import (
    FilenameCaseRule,
    FolderKebabCaseRule,
    NameKebabCaseRule,
    NameMatchesFolderRule,
    NameNoReservedRule,
)
from skillet.lint.types import LintSeverity, SkillDocument


def _doc(
    name: str = "my-skill",
    description: str = "A skill.",
    path: Path | None = None,
) -> SkillDocument:
    if path is None:
        path = Path("my-skill/SKILL.md")
    return SkillDocument(
        path=path,
        content="",
        frontmatter={"name": name, "description": description},
        body="",
    )


def describe_filename_case_rule():
    rule = FilenameCaseRule()

    def it_passes_for_SKILL_md():
        findings = rule.check(_doc(path=Path("my-skill/SKILL.md")))
        assert findings == []

    @pytest.mark.parametrize(
        "filename",
        ["skill.md", "Skill.md", "SKILL.MD", "Skill.MD", "skill.MD"],
    )
    def it_warns_on_wrong_case(filename: str):
        findings = rule.check(_doc(path=Path(f"my-skill/{filename}")))
        assert len(findings) == 1
        assert findings[0].severity == LintSeverity.WARNING
        assert findings[0].rule == "filename-case"


def describe_folder_kebab_case_rule():
    rule = FolderKebabCaseRule()

    @pytest.mark.parametrize(
        "folder",
        ["my-skill", "browser-fallback", "a", "skill-123", "a-b-c"],
    )
    def it_passes_for_kebab_case(folder: str):
        findings = rule.check(_doc(path=Path(f"{folder}/SKILL.md")))
        assert findings == []

    @pytest.mark.parametrize(
        "folder",
        ["My-Skill", "my_skill", "mySkill", "My Skill", "MY-SKILL", "my--skill"],
    )
    def it_warns_on_non_kebab_case(folder: str):
        findings = rule.check(_doc(path=Path(f"{folder}/SKILL.md")))
        assert len(findings) == 1
        assert findings[0].severity == LintSeverity.WARNING
        assert findings[0].rule == "folder-kebab-case"


def describe_name_kebab_case_rule():
    rule = NameKebabCaseRule()

    @pytest.mark.parametrize(
        "name",
        ["my-skill", "browser-fallback", "a", "skill-123"],
    )
    def it_passes_for_kebab_case(name: str):
        findings = rule.check(_doc(name=name))
        assert findings == []

    @pytest.mark.parametrize(
        "name",
        ["My-Skill", "my_skill", "mySkill", "My Skill", "MY-SKILL"],
    )
    def it_warns_on_non_kebab_case(name: str):
        findings = rule.check(_doc(name=name))
        assert len(findings) == 1
        assert findings[0].severity == LintSeverity.WARNING
        assert findings[0].rule == "name-kebab-case"

    def it_skips_when_name_missing():
        doc = SkillDocument(
            path=Path("my-skill/SKILL.md"),
            content="",
            frontmatter={},
            body="",
        )
        findings = rule.check(doc)
        assert findings == []


def describe_name_matches_folder_rule():
    rule = NameMatchesFolderRule()

    def it_passes_when_name_matches_folder():
        findings = rule.check(_doc(name="my-skill", path=Path("my-skill/SKILL.md")))
        assert findings == []

    def it_warns_when_name_differs_from_folder():
        findings = rule.check(_doc(name="other-name", path=Path("my-skill/SKILL.md")))
        assert len(findings) == 1
        assert findings[0].severity == LintSeverity.WARNING
        assert findings[0].rule == "name-matches-folder"

    def it_skips_when_name_missing():
        doc = SkillDocument(
            path=Path("my-skill/SKILL.md"),
            content="",
            frontmatter={},
            body="",
        )
        findings = rule.check(doc)
        assert findings == []


def describe_name_no_reserved_rule():
    rule = NameNoReservedRule()

    def it_passes_for_normal_names():
        findings = rule.check(_doc(name="my-skill"))
        assert findings == []

    @pytest.mark.parametrize(
        "name",
        ["claude-helper", "my-anthropic-tool", "claude", "anthropic", "Claude-Skill"],
    )
    def it_errors_on_reserved_words(name: str):
        findings = rule.check(_doc(name=name))
        assert len(findings) == 1
        assert findings[0].severity == LintSeverity.ERROR
        assert findings[0].rule == "name-no-reserved"

    def it_skips_when_name_missing():
        doc = SkillDocument(
            path=Path("my-skill/SKILL.md"),
            content="",
            frontmatter={},
            body="",
        )
        findings = rule.check(doc)
        assert findings == []
