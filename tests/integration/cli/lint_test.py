"""Integration tests for the `skillet lint` command."""

from pathlib import Path

import pytest

from skillet.errors import LintError
from skillet.lint import lint_skill


def _write_skill(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


VALID_SKILL = """\
---
name: test-skill
description: A test skill for linting.
license: MIT
compatibility: ">=1.0"
metadata:
  author: test
---

# Instructions

Do the thing.
"""

MISSING_NAME_SKILL = """\
---
description: A test skill without a name.
---

# Instructions

Do the thing.
"""

MISSING_DESCRIPTION_SKILL = """\
---
name: test-skill
---

# Instructions

Do the thing.
"""

XML_IN_FRONTMATTER = """\
---
name: test-skill
description: <b>Bold</b> description
---

Body here.
"""

NO_FRONTMATTER_DELIMITERS = """\
name: test-skill
description: A skill.

Body here.
"""

RESERVED_NAME_SKILL = """\
---
name: claude-helper
description: A skill.
---

Body here.
"""


def describe_lint_skill():
    """Integration tests for lint_skill function."""

    def it_returns_no_findings_for_valid_skill(tmp_path: Path):
        skill_path = _write_skill(tmp_path / "test-skill" / "SKILL.md", VALID_SKILL)
        result = lint_skill(skill_path)
        assert result.findings == []

    def it_raises_lint_error_for_missing_file(tmp_path: Path):
        with pytest.raises(LintError):
            lint_skill(tmp_path / "nonexistent" / "SKILL.md")

    def it_finds_missing_name(tmp_path: Path):
        skill_path = _write_skill(tmp_path / "test-skill" / "SKILL.md", MISSING_NAME_SKILL)
        result = lint_skill(skill_path)
        rules = [f.rule for f in result.findings]
        assert "frontmatter-valid" in rules

    def it_finds_missing_description(tmp_path: Path):
        skill_path = _write_skill(tmp_path / "test-skill" / "SKILL.md", MISSING_DESCRIPTION_SKILL)
        result = lint_skill(skill_path)
        rules = [f.rule for f in result.findings]
        assert "frontmatter-valid" in rules

    def it_finds_xml_in_frontmatter(tmp_path: Path):
        skill_path = _write_skill(tmp_path / "test-skill" / "SKILL.md", XML_IN_FRONTMATTER)
        result = lint_skill(skill_path)
        rules = [f.rule for f in result.findings]
        assert "frontmatter-no-xml" in rules

    def it_finds_missing_frontmatter_delimiters(tmp_path: Path):
        skill_path = _write_skill(tmp_path / "test-skill" / "SKILL.md", NO_FRONTMATTER_DELIMITERS)
        result = lint_skill(skill_path)
        rules = [f.rule for f in result.findings]
        assert "frontmatter-delimiters" in rules

    def it_finds_reserved_name(tmp_path: Path):
        skill_path = _write_skill(tmp_path / "claude-helper" / "SKILL.md", RESERVED_NAME_SKILL)
        result = lint_skill(skill_path)
        rules = [f.rule for f in result.findings]
        assert "name-no-reserved" in rules

    def it_finds_name_folder_mismatch(tmp_path: Path):
        skill_path = _write_skill(tmp_path / "wrong-folder" / "SKILL.md", VALID_SKILL)
        result = lint_skill(skill_path)
        rules = [f.rule for f in result.findings]
        assert "name-matches-folder" in rules

    def it_warns_on_readme_in_skill_folder(tmp_path: Path):
        skill_path = _write_skill(tmp_path / "test-skill" / "SKILL.md", VALID_SKILL)
        (tmp_path / "test-skill" / "README.md").write_text("# Readme")
        result = lint_skill(skill_path)
        rules = [f.rule for f in result.findings]
        assert "no-readme" in rules

    def it_finds_wrong_filename_case(tmp_path: Path):
        skill_path = _write_skill(tmp_path / "test-skill" / "skill.md", VALID_SKILL)
        result = lint_skill(skill_path)
        rules = [f.rule for f in result.findings]
        assert "filename-case" in rules

    def it_finds_non_kebab_folder(tmp_path: Path):
        skill_path = _write_skill(tmp_path / "TestSkill" / "SKILL.md", VALID_SKILL)
        result = lint_skill(skill_path)
        rules = [f.rule for f in result.findings]
        assert "folder-kebab-case" in rules

    def it_finds_missing_recommended_fields(tmp_path: Path):
        content = """\
---
name: test-skill
description: A skill.
---

Body.
"""
        skill_path = _write_skill(tmp_path / "test-skill" / "SKILL.md", content)
        result = lint_skill(skill_path)
        rules = [f.rule for f in result.findings]
        assert "field-license" in rules
        assert "field-compatibility" in rules
        assert "field-metadata" in rules
