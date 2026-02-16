"""End-to-end tests for the `skillet lint` command."""

from collections.abc import Callable
from pathlib import Path

from curtaincall import Terminal, expect


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

    def it_exits_0_for_valid_skill(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        skill_path = _write_skill(tmp_path, "test-skill", VALID_SKILL)
        term = terminal(f"skillet lint --no-llm {skill_path}")
        expect(term).to_have_exited()
        assert term.exit_code == 0

    def it_exits_2_for_missing_file(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        term = terminal(f"skillet lint {tmp_path / 'nonexistent' / 'SKILL.md'}")
        expect(term).to_have_exited()
        assert term.exit_code == 2

    def it_exits_1_when_findings_exist(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        skill_path = _write_skill(tmp_path, "test-skill", MISSING_NAME_SKILL)
        term = terminal(f"skillet lint --no-llm {skill_path}")
        expect(term).to_have_exited()
        assert term.exit_code == 1

    def it_lists_rules(terminal: Callable[..., Terminal]):
        term = terminal("skillet lint --list-rules")
        expect(term).to_have_exited()
        assert term.exit_code == 0
        expect(term.get_by_text("frontmatter-valid")).to_be_visible()
        expect(term.get_by_text("filename-case")).to_be_visible()

    def it_shows_finding_details_in_output(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        skill_path = _write_skill(tmp_path, "test-skill", MISSING_NAME_SKILL)
        term = terminal(f"skillet lint --no-llm {skill_path}")
        expect(term).to_have_exited()
        assert (
            term.get_by_text("frontmatter-valid").is_visible()
            or term.get_by_text("name").is_visible()
        )

    def it_accepts_no_llm_flag(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        skill_path = _write_skill(tmp_path, "test-skill", VALID_SKILL)
        term = terminal(f"skillet lint --no-llm {skill_path}")
        expect(term).to_have_exited()
        assert term.exit_code == 0
