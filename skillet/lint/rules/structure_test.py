"""Tests for structure lint rules."""

from pathlib import Path

from skillet.lint.rules.structure import (
    BodyWordCountRule,
    DescriptionLengthRule,
    FrontmatterDelimitersRule,
    FrontmatterNoXmlRule,
    NoReadmeRule,
)
from skillet.lint.types import LintSeverity, SkillDocument


def _doc(
    content: str = "---\nname: x\n---\n",
    frontmatter: dict | None = None,
    body: str = "",
    path: Path | None = None,
) -> SkillDocument:
    if frontmatter is None:
        frontmatter = {"name": "x", "description": "y"}
    if path is None:
        path = Path("my-skill/SKILL.md")
    return SkillDocument(
        path=path,
        content=content,
        frontmatter=frontmatter,
        body=body,
    )


def describe_frontmatter_delimiters_rule():
    rule = FrontmatterDelimitersRule()

    def it_passes_with_valid_delimiters():
        findings = rule.check(_doc(content="---\nname: x\n---\nbody"))
        assert findings == []

    def it_errors_when_no_opening_delimiter():
        findings = rule.check(_doc(content="name: x\n---\nbody"))
        assert len(findings) == 1
        assert findings[0].severity == LintSeverity.ERROR
        assert findings[0].rule == "frontmatter-delimiters"

    def it_errors_when_no_closing_delimiter():
        findings = rule.check(_doc(content="---\nname: x\nbody"))
        assert len(findings) == 1
        assert findings[0].severity == LintSeverity.ERROR


def describe_frontmatter_no_xml_rule():
    rule = FrontmatterNoXmlRule()

    def it_passes_with_clean_frontmatter():
        findings = rule.check(_doc(content="---\nname: my-skill\ndescription: A skill\n---\n"))
        assert findings == []

    def it_errors_on_angle_brackets_in_frontmatter():
        findings = rule.check(_doc(content="---\nname: <my-skill>\ndescription: A skill\n---\n"))
        assert len(findings) == 1
        assert findings[0].severity == LintSeverity.ERROR
        assert findings[0].rule == "frontmatter-no-xml"

    def it_ignores_angle_brackets_in_body():
        findings = rule.check(_doc(content="---\nname: my-skill\n---\n<div>body</div>"))
        assert findings == []

    def it_ignores_greater_than_in_yaml_values():
        findings = rule.check(_doc(content='---\ncompatibility: ">=1.0"\n---\n'))
        assert findings == []

    def it_passes_when_no_frontmatter():
        findings = rule.check(_doc(content="no frontmatter here"))
        assert findings == []


def describe_no_readme_rule():
    rule = NoReadmeRule()

    def it_passes_when_no_readme(tmp_path: Path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("---\nname: x\n---\n")

        findings = rule.check(_doc(path=skill_file))
        assert findings == []

    def it_warns_when_readme_exists(tmp_path: Path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("---\nname: x\n---\n")
        (skill_dir / "README.md").write_text("# Readme")

        findings = rule.check(_doc(path=skill_file))
        assert len(findings) == 1
        assert findings[0].severity == LintSeverity.WARNING
        assert findings[0].rule == "no-readme"


def describe_body_word_count_rule():
    rule = BodyWordCountRule()

    def it_passes_under_limit():
        findings = rule.check(_doc(body="word " * 100))
        assert findings == []

    def it_warns_over_5000_words():
        findings = rule.check(_doc(body="word " * 5001))
        assert len(findings) == 1
        assert findings[0].severity == LintSeverity.WARNING
        assert findings[0].rule == "body-word-count"


def describe_description_length_rule():
    rule = DescriptionLengthRule()

    def it_passes_under_limit():
        findings = rule.check(_doc(frontmatter={"description": "short"}))
        assert findings == []

    def it_warns_over_1024_chars():
        findings = rule.check(_doc(frontmatter={"description": "x" * 1025}))
        assert len(findings) == 1
        assert findings[0].severity == LintSeverity.WARNING
        assert findings[0].rule == "description-length"

    def it_skips_when_description_missing():
        findings = rule.check(_doc(frontmatter={}))
        assert findings == []
