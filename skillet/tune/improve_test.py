"""Tests for tune/improve module."""

import tempfile
from pathlib import Path

from skillet.tune.improve import TUNE_TIPS, get_skill_file


def describe_TUNE_TIPS():
    """Tests for TUNE_TIPS constant."""

    def it_has_multiple_tips():
        assert len(TUNE_TIPS) > 0

    def it_contains_strings():
        for tip in TUNE_TIPS:
            assert isinstance(tip, str)
            assert len(tip) > 0


def describe_get_skill_file():
    """Tests for get_skill_file function."""

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
            # Don't create SKILL.md

            result = get_skill_file(skill_dir)
            assert result == skill_dir / "SKILL.md"
