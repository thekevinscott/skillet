"""Tests for parse_skill."""

from pathlib import Path

from skillet.lint.parse import parse_skill

VALID_SKILL = """\
---
name: test
description: A test.
---

Body text.
"""

NO_FRONTMATTER_SKILL = """\
# Just a heading

No frontmatter here.
"""

MALFORMED_YAML_SKILL = """\
---
: invalid: yaml: [[
---

Body.
"""


def describe_parse_skill():
    def it_parses_valid_frontmatter(tmp_path: Path):
        skill = tmp_path / "SKILL.md"
        skill.write_text(VALID_SKILL)

        doc = parse_skill(skill)

        assert doc.frontmatter == {"name": "test", "description": "A test."}
        assert "Body text." in doc.body
        assert doc.path == skill

    def it_returns_empty_frontmatter_when_missing(tmp_path: Path):
        skill = tmp_path / "SKILL.md"
        skill.write_text(NO_FRONTMATTER_SKILL)

        doc = parse_skill(skill)

        assert doc.frontmatter == {}
        assert "Just a heading" in doc.body

    def it_returns_empty_frontmatter_for_malformed_yaml(tmp_path: Path):
        skill = tmp_path / "SKILL.md"
        skill.write_text(MALFORMED_YAML_SKILL)

        doc = parse_skill(skill)

        assert doc.frontmatter == {}
