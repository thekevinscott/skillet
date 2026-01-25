"""Tests for tune/improve module."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from skillet.skill.models import SkillContent
from skillet.tune.improve import TUNE_TIPS, get_skill_file, improve_skill


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


def describe_improve_skill():
    """Tests for improve_skill function."""

    @pytest.fixture(autouse=True)
    def mock_query_structured():
        with patch("skillet.tune.improve.query_structured", new_callable=AsyncMock) as mock:
            mock.return_value = SkillContent(content="# Improved Skill")
            yield mock

    @pytest.mark.asyncio
    async def it_reads_current_skill_content(mock_query_structured):
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "SKILL.md"
            skill_path.write_text("# Original Skill")

            failures = [{"prompt": "p", "expected": "e", "judgment": {"reasoning": "fail"}}]
            result = await improve_skill(skill_path, failures)

            assert result == "# Improved Skill"
            # Check original content was included in prompt
            call_args = mock_query_structured.call_args
            prompt = call_args[0][0]
            assert "# Original Skill" in prompt

    @pytest.mark.asyncio
    async def it_includes_failures_in_prompt(mock_query_structured):
        mock_query_structured.return_value = SkillContent(content="# Better Skill")

        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "SKILL.md"
            skill_path.write_text("# Skill")

            failures = [
                {
                    "prompt": "Say hello",
                    "expected": "Greeting",
                    "response": "Wrong answer",
                    "judgment": {"reasoning": "Did not greet"},
                }
            ]
            await improve_skill(skill_path, failures)

            call_args = mock_query_structured.call_args
            prompt = call_args[0][0]
            assert "Say hello" in prompt
            assert "Greeting" in prompt

    @pytest.mark.asyncio
    async def it_includes_tip_when_provided(mock_query_structured):
        mock_query_structured.return_value = SkillContent(content="# Terse Skill")

        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "SKILL.md"
            skill_path.write_text("# Skill")

            failures = [{"prompt": "p", "expected": "e", "judgment": {"reasoning": "r"}}]
            await improve_skill(skill_path, failures, tip="Be extremely terse")

            call_args = mock_query_structured.call_args
            prompt = call_args[0][0]
            assert "Be extremely terse" in prompt

    @pytest.mark.asyncio
    async def it_extracts_content_from_structured_output(mock_query_structured):
        mock_query_structured.return_value = SkillContent(content="# Clean Skill")

        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "SKILL.md"
            skill_path.write_text("# Old")

            failures = [{"prompt": "p", "expected": "e", "judgment": {"reasoning": "r"}}]
            result = await improve_skill(skill_path, failures)

            assert result == "# Clean Skill"

    @pytest.mark.asyncio
    async def it_handles_skill_directory_input(mock_query_structured):
        mock_query_structured.return_value = SkillContent(content="# Result")

        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir)
            (skill_dir / "SKILL.md").write_text("# Directory Skill")

            failures = [{"prompt": "p", "expected": "e", "judgment": {"reasoning": "r"}}]
            result = await improve_skill(skill_dir, failures)

            assert result == "# Result"
            call_args = mock_query_structured.call_args
            prompt = call_args[0][0]
            assert "# Directory Skill" in prompt
