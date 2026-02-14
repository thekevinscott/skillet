"""End-to-end tests for the `skillet lint` command."""

import subprocess
from pathlib import Path


def _run_lint(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["skillet", "lint", *args],
        capture_output=True,
        text=True,
        timeout=30,
    )


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

MISSING_NAME_SKILL = """\
---
description: A test skill without a name.
---

# Instructions

Do the thing.
"""


def describe_skillet_lint():
    """Tests for the `skillet lint` command."""

    def it_exits_0_for_valid_skill(tmp_path: Path):
        skill_path = _write_skill(tmp_path, "test-skill", VALID_SKILL)
        result = _run_lint("--no-llm", str(skill_path))
        assert result.returncode == 0, (
            f"Expected exit 0 for valid skill\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def it_exits_2_for_missing_file(tmp_path: Path):
        result = _run_lint(str(tmp_path / "nonexistent" / "SKILL.md"))
        assert result.returncode == 2, (
            f"Expected exit 2 for missing file\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def it_exits_1_when_findings_exist(tmp_path: Path):
        skill_path = _write_skill(tmp_path, "test-skill", MISSING_NAME_SKILL)
        result = _run_lint("--no-llm", str(skill_path))
        assert result.returncode == 1, (
            f"Expected exit 1 for findings\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def it_lists_rules():
        result = _run_lint("--list-rules")
        assert result.returncode == 0, (
            f"Expected exit 0 for --list-rules\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
        assert "frontmatter-valid" in result.stdout
        assert "filename-case" in result.stdout

    def it_shows_finding_details_in_output(tmp_path: Path):
        skill_path = _write_skill(tmp_path, "test-skill", MISSING_NAME_SKILL)
        result = _run_lint("--no-llm", str(skill_path))
        assert "frontmatter-valid" in result.stdout or "name" in result.stdout

    def it_accepts_no_llm_flag(tmp_path: Path):
        skill_path = _write_skill(tmp_path, "test-skill", VALID_SKILL)
        result = _run_lint("--no-llm", str(skill_path))
        assert result.returncode == 0, (
            f"--no-llm should work\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
