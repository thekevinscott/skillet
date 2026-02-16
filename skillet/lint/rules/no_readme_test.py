"""Tests for NoReadmeRule."""

from pathlib import Path

from skillet.lint.rules.no_readme import NoReadmeRule
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
