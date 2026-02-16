"""Tests for NameMatchesFolderRule."""

from pathlib import Path

from skillet.lint.rules.name_matches_folder import NameMatchesFolderRule
from skillet.lint.types import SkillDocument


def _doc(path: str = "my-skill/SKILL.md", name: str = "my-skill") -> SkillDocument:
    return SkillDocument(
        path=Path(path),
        content="",
        frontmatter={"name": name, "description": "A test skill."},
        body="",
    )


def describe_name_matches_folder_rule():
    def it_passes_when_name_matches_folder():
        assert NameMatchesFolderRule().check(_doc("my-skill/SKILL.md", name="my-skill")) == []

    def it_warns_when_name_differs_from_folder():
        findings = NameMatchesFolderRule().check(_doc("my-skill/SKILL.md", name="other-name"))
        assert len(findings) == 1
        assert findings[0].rule == "name-matches-folder"
        assert "other-name" in findings[0].message
        assert "my-skill" in findings[0].message

    def it_skips_when_name_missing():
        assert NameMatchesFolderRule().check(_doc(name="")) == []
