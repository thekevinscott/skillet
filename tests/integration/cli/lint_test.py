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


def describe_lint_skill():
    """Integration tests for lint_skill function."""

    def it_returns_no_findings_for_valid_skill(tmp_path: Path):
        skill_path = _write_skill(tmp_path / "SKILL.md", VALID_SKILL)
        result = lint_skill(skill_path)
        assert result.findings == []

    def it_raises_lint_error_for_missing_file(tmp_path: Path):
        with pytest.raises(LintError):
            lint_skill(tmp_path / "nonexistent" / "SKILL.md")

    def it_finds_missing_name(tmp_path: Path):
        skill_path = _write_skill(tmp_path / "SKILL.md", MISSING_NAME_SKILL)
        result = lint_skill(skill_path)
        assert len(result.findings) == 1
        assert result.findings[0].rule == "frontmatter-valid"
        assert "name" in result.findings[0].message

    def it_finds_missing_description(tmp_path: Path):
        skill_path = _write_skill(tmp_path / "SKILL.md", MISSING_DESCRIPTION_SKILL)
        result = lint_skill(skill_path)
        assert len(result.findings) == 1
        assert result.findings[0].rule == "frontmatter-valid"
        assert "description" in result.findings[0].message
