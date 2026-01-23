"""Integration tests for the lint API."""

from pathlib import Path

import pytest

from skillet.errors import LintError, SkillParseError
from skillet.lint import LintSeverity, lint

VALID_SKILL = """\
---
name: test-skill
description: A valid test skill
---

# Role

You are a helpful assistant.

# Goals

- Help users effectively

# Instructions

Follow best practices.
"""

SKILL_MISSING_FRONTMATTER = """\
# No Frontmatter

This skill has no YAML frontmatter.
"""

SKILL_MISSING_DESCRIPTION = """\
---
name: test-skill
---

# Instructions

Do things.
"""

SKILL_WITH_VAGUE_LANGUAGE = """\
---
name: test-skill
description: A test skill
---

Handle errors properly.

Process data correctly as needed.
"""

SKILL_OVERSIZED = """\
---
name: test-skill
description: A test skill
---
""" + "\n".join([f"Line {i}" for i in range(500)])


def describe_lint():
    """Integration tests for lint function."""

    def it_returns_empty_findings_for_valid_skill(tmp_path: Path):
        """Happy path: valid skill has no errors or warnings."""
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(VALID_SKILL)

        result = lint(skill_dir)

        assert result.error_count == 0
        assert result.warning_count == 0
        # May have suggestions for missing examples, that's ok

    def it_detects_missing_frontmatter(tmp_path: Path):
        """Detects when YAML frontmatter is missing."""
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(SKILL_MISSING_FRONTMATTER)

        result = lint(skill_dir)

        assert result.error_count >= 1
        frontmatter_errors = [
            f for f in result.findings
            if f.rule_id == "frontmatter-valid" and f.severity == LintSeverity.ERROR
        ]
        assert len(frontmatter_errors) >= 1
        assert "frontmatter" in frontmatter_errors[0].message.lower()

    def it_detects_missing_required_fields(tmp_path: Path):
        """Detects missing required frontmatter fields."""
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(SKILL_MISSING_DESCRIPTION)

        result = lint(skill_dir)

        assert result.error_count >= 1
        missing_field_errors = [
            f for f in result.findings
            if f.rule_id == "frontmatter-valid" and "description" in f.message.lower()
        ]
        assert len(missing_field_errors) == 1

    def it_detects_vague_language(tmp_path: Path):
        """Detects vague language like 'properly', 'correctly'."""
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(SKILL_WITH_VAGUE_LANGUAGE)

        result = lint(skill_dir)

        vague_warnings = [
            f for f in result.findings if f.rule_id == "vague-language"
        ]
        assert len(vague_warnings) >= 2
        messages = " ".join(f.message for f in vague_warnings)
        assert "properly" in messages
        assert "correctly" in messages

    def it_detects_oversized_skill(tmp_path: Path):
        """Detects skill files exceeding size limits."""
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(SKILL_OVERSIZED)

        result = lint(skill_dir)

        size_findings = [f for f in result.findings if f.rule_id == "size-limit"]
        assert len(size_findings) == 1
        assert size_findings[0].severity == LintSeverity.ERROR

    def it_raises_error_for_nonexistent_path(tmp_path: Path):
        """Raises LintError for non-existent paths."""
        nonexistent = tmp_path / "nonexistent"

        with pytest.raises(LintError, match="does not exist"):
            lint(nonexistent)

    def it_raises_error_for_directory_without_skill_md(tmp_path: Path):
        """Raises LintError when directory has no SKILL.md."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with pytest.raises(LintError, match=r"No SKILL\.md found"):
            lint(empty_dir)

    def it_accepts_direct_path_to_skill_md(tmp_path: Path):
        """Can lint a direct path to SKILL.md file."""
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        skill_path = skill_dir / "SKILL.md"
        skill_path.write_text(VALID_SKILL)

        result = lint(skill_path)

        assert result.path == skill_path
        assert result.error_count == 0

    def it_respects_disabled_rules(tmp_path: Path):
        """Disabled rules don't produce findings."""
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(SKILL_WITH_VAGUE_LANGUAGE)

        result = lint(skill_dir, disabled_rules=["vague-language"])

        vague_findings = [f for f in result.findings if f.rule_id == "vague-language"]
        assert len(vague_findings) == 0

    def it_raises_error_for_unknown_disabled_rule(tmp_path: Path):
        """Raises LintError for unknown rule IDs in disabled_rules."""
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(VALID_SKILL)

        with pytest.raises(LintError, match="Unknown rule IDs"):
            lint(skill_dir, disabled_rules=["nonexistent-rule"])

    def it_raises_error_for_invalid_yaml_frontmatter(tmp_path: Path):
        """Raises SkillParseError for malformed YAML."""
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: [invalid yaml\n---\n")

        with pytest.raises(SkillParseError, match="Invalid YAML"):
            lint(skill_dir)


def describe_lint_cli():
    """Tests for lint CLI command handler."""

    def it_returns_exit_code_0_for_valid_skill(tmp_path: Path):
        """Exit code 0 when no findings above threshold."""
        from skillet.cli.commands.lint import lint_command

        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(VALID_SKILL)

        exit_code = lint_command(skill_dir)

        assert exit_code == 0

    def it_returns_exit_code_1_for_errors(tmp_path: Path):
        """Exit code 1 when errors found."""
        from skillet.cli.commands.lint import lint_command

        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(SKILL_MISSING_DESCRIPTION)

        exit_code = lint_command(skill_dir)

        assert exit_code == 1

    def it_returns_exit_code_1_when_fail_on_warning(tmp_path: Path):
        """Exit code 1 when warnings found and fail_on='warning'."""
        from skillet.cli.commands.lint import lint_command

        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(SKILL_WITH_VAGUE_LANGUAGE)

        exit_code = lint_command(skill_dir, fail_on="warning")

        assert exit_code == 1

    def it_returns_exit_code_0_when_warnings_below_threshold(tmp_path: Path):
        """Exit code 0 when warnings found but fail_on='error'."""
        from skillet.cli.commands.lint import lint_command

        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(SKILL_WITH_VAGUE_LANGUAGE)

        exit_code = lint_command(skill_dir, fail_on="error")

        assert exit_code == 0

    def it_returns_exit_code_2_for_missing_path(tmp_path: Path):
        """Exit code 2 when path doesn't exist."""
        from skillet.cli.commands.lint import lint_command

        exit_code = lint_command(tmp_path / "nonexistent")

        assert exit_code == 2

    def it_outputs_json_format(tmp_path: Path, capsys):
        """JSON format output is valid JSON."""
        import json

        from skillet.cli.commands.lint import lint_command

        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(SKILL_MISSING_DESCRIPTION)

        lint_command(skill_dir, format="json")

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "findings" in data
        assert "summary" in data
        assert data["summary"]["errors"] >= 1

    def it_lists_rules(capsys):
        """--list-rules shows available rules."""
        from skillet.cli.commands.lint import lint_command

        exit_code = lint_command(None, list_rules=True)

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "frontmatter-valid" in captured.out
        assert "vague-language" in captured.out
