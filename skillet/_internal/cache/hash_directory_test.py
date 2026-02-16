"""Tests for hash_directory function."""

import tempfile
from pathlib import Path

from skillet._internal.cache import hash_directory


def describe_hash_directory():
    def it_is_deterministic():
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir)
            (skill_dir / "SKILL.md").write_text("# Test Skill\n")

            hash1 = hash_directory(skill_dir)
            hash2 = hash_directory(skill_dir)
            assert hash1 == hash2

    def it_changes_on_content_change():
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir)
            (skill_dir / "SKILL.md").write_text("# Test Skill v1\n")
            hash1 = hash_directory(skill_dir)

            hash_directory.cache_clear()

            (skill_dir / "SKILL.md").write_text("# Test Skill v2\n")
            hash2 = hash_directory(skill_dir)

            assert hash1 != hash2

    def it_returns_cached_result_on_repeated_calls():
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir)
            (skill_dir / "SKILL.md").write_text("# Test Skill\n")

            hash_directory.cache_clear()

            hash_directory(skill_dir)
            hash_directory(skill_dir)
            hash_directory(skill_dir)

            info = hash_directory.cache_info()
            assert info.hits == 2
            assert info.misses == 1

    def it_falls_back_to_hash_file_for_non_directory():
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "skill.md"
            path.write_text("# Skill content")
            result = hash_directory(path)
            assert len(result) == 12

    def it_includes_multiple_files():
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir)
            (skill_dir / "SKILL.md").write_text("# Main skill")
            (skill_dir / "extra.md").write_text("# Extra content")

            hash1 = hash_directory(skill_dir)

            hash_directory.cache_clear()

            # Changing any file should change the hash
            (skill_dir / "extra.md").write_text("# Modified extra")
            hash2 = hash_directory(skill_dir)

            assert hash1 != hash2
