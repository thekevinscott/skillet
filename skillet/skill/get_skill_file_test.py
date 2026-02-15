"""Tests for skill/get_skill_file module."""

import tempfile
from pathlib import Path

from skillet.skill.get_skill_file import get_skill_file


def describe_get_skill_file():
    def it_returns_file_path_directly_when_given_file():
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "skill.md"
            path.write_text("# Skill content")
            result = get_skill_file(path)
            assert result == path

    def it_returns_skill_md_when_given_directory():
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir)
            (skill_dir / "SKILL.md").write_text("# Test skill")

            result = get_skill_file(skill_dir)
            assert result == skill_dir / "SKILL.md"

    def it_returns_skill_md_path_even_if_not_exists():
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir)

            result = get_skill_file(skill_dir)
            assert result == skill_dir / "SKILL.md"
