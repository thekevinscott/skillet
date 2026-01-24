"""Tests for parse_skill function."""

from pathlib import Path

import pytest

from skillet.errors import SkillParseError

from .parse import parse_skill


def describe_parse_skill():
    """Tests for parse_skill function."""

    def it_parses_valid_skill_with_frontmatter(tmp_path: Path):
        skill_path = tmp_path / "SKILL.md"
        skill_path.write_text("---\nname: test\ndescription: desc\n---\n\nBody content.")

        doc = parse_skill(skill_path)

        assert doc.path == skill_path
        assert doc.frontmatter == {"name": "test", "description": "desc"}
        assert "Body content" in doc.body
        assert doc.frontmatter_end_line == 4

    def it_parses_skill_without_frontmatter(tmp_path: Path):
        skill_path = tmp_path / "SKILL.md"
        skill_path.write_text("# No frontmatter\n\nJust body.")

        doc = parse_skill(skill_path)

        assert doc.frontmatter is None
        assert doc.body == "# No frontmatter\n\nJust body."
        assert doc.frontmatter_end_line == 0

    def it_raises_for_nonexistent_file(tmp_path: Path):
        with pytest.raises(SkillParseError, match="File not found"):
            parse_skill(tmp_path / "nonexistent.md")

    def it_raises_for_directory(tmp_path: Path):
        with pytest.raises(SkillParseError, match="Not a file"):
            parse_skill(tmp_path)

    def it_raises_for_invalid_yaml(tmp_path: Path):
        skill_path = tmp_path / "SKILL.md"
        skill_path.write_text("---\nname: [invalid\n---\n")

        with pytest.raises(SkillParseError, match="Invalid YAML"):
            parse_skill(skill_path)

    def it_counts_lines_correctly(tmp_path: Path):
        skill_path = tmp_path / "SKILL.md"
        content = "line1\nline2\nline3\nline4\nline5"
        skill_path.write_text(content)

        doc = parse_skill(skill_path)

        assert doc.line_count == 5
