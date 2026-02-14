"""Integration tests for the `skillet lint` command."""

from pathlib import Path

import pytest

from skillet.errors import LintError
from skillet.lint import lint_skill


def _write_skill(base: Path, name: str, content: str) -> Path:
    """Write a SKILL.md inside a properly named folder."""
    folder = base / name
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "SKILL.md"
    path.write_text(content)
    return path


VALID_SKILL = """\
---
name: test-skill
description: A test skill for linting.
license: MIT
compatibility: claude-code
metadata:
  version: 1
---

# Instructions

Do the thing.
"""

MINIMAL_SKILL = """\
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

NO_FRONTMATTER_SKILL = """\
# Instructions

Do the thing.
"""

XML_IN_FRONTMATTER_SKILL = """\
---
name: test-skill
description: Uses <xml> tags.
---

# Instructions

Do the thing.
"""

RESERVED_NAME_SKILL = """\
---
name: claude-helper
description: A skill with a reserved name.
---

# Instructions

Do the thing.
"""


def describe_lint_skill():
    """Integration tests for lint_skill — no mocks, real rules."""

    @pytest.mark.asyncio
    async def it_returns_no_findings_for_valid_skill(tmp_path: Path):
        skill_path = _write_skill(tmp_path, "test-skill", VALID_SKILL)
        result = await lint_skill(skill_path)
        assert result.findings == [], [f.rule for f in result.findings]

    @pytest.mark.asyncio
    async def it_raises_lint_error_for_missing_file(tmp_path: Path):
        with pytest.raises(LintError):
            await lint_skill(tmp_path / "nonexistent" / "SKILL.md")

    @pytest.mark.asyncio
    async def it_finds_missing_name(tmp_path: Path):
        skill_path = _write_skill(tmp_path, "test-skill", MISSING_NAME_SKILL)
        result = await lint_skill(skill_path, include_llm=False)
        rules = [f.rule for f in result.findings]
        assert "frontmatter-valid" in rules

    @pytest.mark.asyncio
    async def it_finds_missing_description(tmp_path: Path):
        skill_path = _write_skill(tmp_path, "test-skill", MISSING_DESCRIPTION_SKILL)
        result = await lint_skill(skill_path, include_llm=False)
        rules = [f.rule for f in result.findings]
        assert "frontmatter-valid" in rules

    @pytest.mark.asyncio
    async def it_finds_missing_frontmatter_delimiters(tmp_path: Path):
        skill_path = _write_skill(tmp_path, "test-skill", NO_FRONTMATTER_SKILL)
        result = await lint_skill(skill_path, include_llm=False)
        rules = [f.rule for f in result.findings]
        assert "frontmatter-delimiters" in rules

    @pytest.mark.asyncio
    async def it_finds_xml_in_frontmatter(tmp_path: Path):
        skill_path = _write_skill(tmp_path, "test-skill", XML_IN_FRONTMATTER_SKILL)
        result = await lint_skill(skill_path, include_llm=False)
        rules = [f.rule for f in result.findings]
        assert "frontmatter-no-xml" in rules

    @pytest.mark.asyncio
    async def it_finds_reserved_name(tmp_path: Path):
        skill_path = _write_skill(tmp_path, "claude-helper", RESERVED_NAME_SKILL)
        result = await lint_skill(skill_path, include_llm=False)
        rules = [f.rule for f in result.findings]
        assert "name-no-reserved" in rules

    @pytest.mark.asyncio
    async def it_finds_wrong_filename(tmp_path: Path):
        folder = tmp_path / "test-skill"
        folder.mkdir()
        path = folder / "skill.md"
        path.write_text(VALID_SKILL)

        result = await lint_skill(path, include_llm=False)
        rules = [f.rule for f in result.findings]
        assert "filename-case" in rules

    @pytest.mark.asyncio
    async def it_finds_non_kebab_case_folder(tmp_path: Path):
        skill_path = _write_skill(tmp_path, "TestSkill", VALID_SKILL)
        result = await lint_skill(skill_path, include_llm=False)
        rules = [f.rule for f in result.findings]
        assert "folder-kebab-case" in rules

    @pytest.mark.asyncio
    async def it_finds_name_folder_mismatch(tmp_path: Path):
        skill_path = _write_skill(tmp_path, "wrong-folder", VALID_SKILL)
        result = await lint_skill(skill_path, include_llm=False)
        rules = [f.rule for f in result.findings]
        assert "name-matches-folder" in rules

    @pytest.mark.asyncio
    async def it_finds_readme_in_skill_folder(tmp_path: Path):
        skill_path = _write_skill(tmp_path, "test-skill", VALID_SKILL)
        (skill_path.parent / "README.md").write_text("# Readme")

        result = await lint_skill(skill_path, include_llm=False)
        rules = [f.rule for f in result.findings]
        assert "no-readme" in rules

    @pytest.mark.asyncio
    async def it_finds_missing_recommended_fields(tmp_path: Path):
        skill_path = _write_skill(tmp_path, "test-skill", MINIMAL_SKILL)
        result = await lint_skill(skill_path, include_llm=False)
        rules = [f.rule for f in result.findings]
        assert "field-license" in rules
        assert "field-compatibility" in rules
        assert "field-metadata" in rules
