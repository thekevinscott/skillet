"""Tests for structure lint rules."""

from pathlib import Path

from skillet.lint.rules.structure import (
    BodyWordCountRule,
    DescriptionLengthRule,
    FrontmatterDelimitersRule,
    FrontmatterNoXmlRule,
    NoReadmeRule,
)
from skillet.lint.types import SkillDocument


def _doc(
    content: str = "---\nname: test\n---\nBody.",
    frontmatter: dict | None = None,
    body: str = "Some body text.",
    path: str = "my-skill/SKILL.md",
) -> SkillDocument:
    if frontmatter is None:
        frontmatter = {"name": "test", "description": "A skill."}
    return SkillDocument(path=Path(path), content=content, frontmatter=frontmatter, body=body)


def describe_frontmatter_delimiters_rule():
    def it_passes_with_valid_delimiters():
        assert FrontmatterDelimitersRule().check(_doc()) == []

    def it_errors_when_missing_opening():
        findings = FrontmatterDelimitersRule().check(_doc(content="name: test\n---\n"))
        assert len(findings) == 1
        assert findings[0].severity.value == "error"

    def it_errors_when_missing_closing():
        findings = FrontmatterDelimitersRule().check(_doc(content="---\nname: test\n"))
        assert len(findings) == 1
        assert "closing" in findings[0].message

    def it_errors_on_empty_content():
        findings = FrontmatterDelimitersRule().check(_doc(content=""))
        assert len(findings) == 1


def describe_frontmatter_no_xml_rule():
    def it_passes_with_clean_frontmatter():
        assert FrontmatterNoXmlRule().check(_doc()) == []

    def it_errors_with_angle_brackets():
        content = "---\ndescription: Use <tool> for work\n---\n"
        findings = FrontmatterNoXmlRule().check(_doc(content=content))
        assert len(findings) == 1
        assert findings[0].severity.value == "error"

    def it_ignores_angle_brackets_in_body():
        content = "---\nname: test\n---\nUse <tool> here."
        assert FrontmatterNoXmlRule().check(_doc(content=content)) == []

    def it_passes_when_no_frontmatter():
        assert FrontmatterNoXmlRule().check(_doc(content="no frontmatter")) == []


def describe_description_length_rule():
    def it_passes_for_short_description():
        assert DescriptionLengthRule().check(_doc()) == []

    def it_warns_for_long_description():
        fm = {"name": "test", "description": "x" * 1025}
        findings = DescriptionLengthRule().check(_doc(frontmatter=fm))
        assert len(findings) == 1
        assert "1025" in findings[0].message

    def it_passes_at_exactly_1024():
        fm = {"name": "test", "description": "x" * 1024}
        assert DescriptionLengthRule().check(_doc(frontmatter=fm)) == []


def describe_body_word_count_rule():
    def it_passes_for_short_body():
        assert BodyWordCountRule().check(_doc()) == []

    def it_warns_for_long_body():
        findings = BodyWordCountRule().check(_doc(body="word " * 5001))
        assert len(findings) == 1
        assert "5001" in findings[0].message

    def it_passes_at_exactly_5000():
        assert BodyWordCountRule().check(_doc(body="word " * 5000)) == []


def describe_no_readme_rule():
    def it_passes_when_no_readme(tmp_path: Path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        skill = skill_dir / "SKILL.md"
        skill.write_text("---\nname: test\n---\n")
        assert NoReadmeRule().check(_doc(path=str(skill))) == []

    def it_warns_when_readme_exists(tmp_path: Path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        skill = skill_dir / "SKILL.md"
        skill.write_text("---\nname: test\n---\n")
        (skill_dir / "README.md").write_text("# Readme")
        findings = NoReadmeRule().check(_doc(path=str(skill)))
        assert len(findings) == 1
        assert findings[0].rule == "no-readme"
