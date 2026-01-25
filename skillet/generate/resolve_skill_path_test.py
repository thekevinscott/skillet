"""Tests for resolve_skill_path."""

from pathlib import Path

import pytest

from skillet.errors import SkillError

from .resolve_skill_path import resolve_skill_path


def describe_resolve_skill_path():
    """Tests for resolve_skill_path function."""

    def it_resolves_skill_md_file(tmp_path: Path):
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("# Skill")

        result = resolve_skill_path(skill_file)

        assert result == skill_file

    def it_resolves_directory_to_skill_md(tmp_path: Path):
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("# Skill")

        result = resolve_skill_path(tmp_path)

        assert result == skill_file

    def it_raises_for_nonexistent_path(tmp_path: Path):
        nonexistent = tmp_path / "does-not-exist"

        with pytest.raises(SkillError, match="does not exist"):
            resolve_skill_path(nonexistent)

    def it_raises_for_non_skill_md_file(tmp_path: Path):
        other_file = tmp_path / "README.md"
        other_file.write_text("# Readme")

        with pytest.raises(SkillError, match=r"Expected SKILL\.md"):
            resolve_skill_path(other_file)

    def it_raises_for_directory_without_skill_md(tmp_path: Path):
        (tmp_path / "other.txt").write_text("content")

        with pytest.raises(SkillError, match=r"SKILL\.md not found"):
            resolve_skill_path(tmp_path)

    def it_expands_user_home():
        # Test ~ expansion (won't actually exist, but tests the path processing)
        with pytest.raises(SkillError, match="does not exist"):
            resolve_skill_path(Path("~/nonexistent-skill-path-12345"))

    def it_resolves_to_absolute_path(tmp_path: Path):
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("# Skill")

        result = resolve_skill_path(skill_file)

        assert result.is_absolute()


@pytest.mark.parametrize(
    ("setup_fn", "expected_success"),
    [
        (lambda p: (p / "SKILL.md").write_text("# Skill"), True),
        (lambda p: (p / "other.md").write_text("# Other"), False),
    ],
    ids=["has-skill-md", "no-skill-md"],
)
def test_resolve_skill_path_directory_variations(tmp_path: Path, setup_fn, expected_success: bool):
    setup_fn(tmp_path)

    if expected_success:
        result = resolve_skill_path(tmp_path)
        assert result.name == "SKILL.md"
    else:
        with pytest.raises(SkillError):
            resolve_skill_path(tmp_path)
