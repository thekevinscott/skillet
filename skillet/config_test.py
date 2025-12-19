"""Tests for config module."""

from pathlib import Path

from skillet.config import CACHE_DIR, DEFAULT_SKILL_TOOLS, MAX_SKILL_LINES, SKILLET_DIR


def describe_config_constants():
    """Tests for configuration constants."""

    def it_has_skillet_dir_in_home():
        assert isinstance(SKILLET_DIR, Path)
        assert ".skillet" in str(SKILLET_DIR)

    def it_has_cache_dir_under_skillet():
        assert isinstance(CACHE_DIR, Path)
        assert "cache" in str(CACHE_DIR)
        assert str(SKILLET_DIR) in str(CACHE_DIR)

    def it_has_default_skill_tools():
        assert isinstance(DEFAULT_SKILL_TOOLS, list)
        assert len(DEFAULT_SKILL_TOOLS) > 0
        assert "Skill" in DEFAULT_SKILL_TOOLS

    def it_has_max_skill_lines_limit():
        assert isinstance(MAX_SKILL_LINES, int)
        assert MAX_SKILL_LINES > 0
