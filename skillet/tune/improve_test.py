"""Tests for tune/improve module."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

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

    @pytest.mark.asyncio
    async def it_reads_current_skill_content():
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch(
                "skillet.tune.improve.query_assistant_text", new_callable=AsyncMock
            ) as mock_query,
        ):
            mock_query.return_value = "# Improved Skill"

            skill_path = Path(tmpdir) / "SKILL.md"
            skill_path.write_text("# Original Skill")

            failures = [{"prompt": "p", "expected": "e", "judgment": {"reasoning": "fail"}}]
            result = await improve_skill(skill_path, failures)

            assert result == "# Improved Skill"
            # Check original content was included in prompt
            call_args = mock_query.call_args
            prompt = call_args[0][0]
            assert "# Original Skill" in prompt

    @pytest.mark.asyncio
    async def it_includes_failures_in_prompt():
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch(
                "skillet.tune.improve.query_assistant_text", new_callable=AsyncMock
            ) as mock_query,
        ):
            mock_query.return_value = "# Better Skill"

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

            call_args = mock_query.call_args
            prompt = call_args[0][0]
            assert "Say hello" in prompt
            assert "Greeting" in prompt

    @pytest.mark.asyncio
    async def it_includes_tip_when_provided():
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch(
                "skillet.tune.improve.query_assistant_text", new_callable=AsyncMock
            ) as mock_query,
        ):
            mock_query.return_value = "# Terse Skill"

            skill_path = Path(tmpdir) / "SKILL.md"
            skill_path.write_text("# Skill")

            failures = [{"prompt": "p", "expected": "e", "judgment": {"reasoning": "r"}}]
            await improve_skill(skill_path, failures, tip="Be extremely terse")

            call_args = mock_query.call_args
            prompt = call_args[0][0]
            assert "Be extremely terse" in prompt

    @pytest.mark.asyncio
    async def it_strips_markdown_from_response():
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch(
                "skillet.tune.improve.query_assistant_text", new_callable=AsyncMock
            ) as mock_query,
        ):
            mock_query.return_value = "```markdown\n# Clean Skill\n```"

            skill_path = Path(tmpdir) / "SKILL.md"
            skill_path.write_text("# Old")

            failures = [{"prompt": "p", "expected": "e", "judgment": {"reasoning": "r"}}]
            result = await improve_skill(skill_path, failures)

            assert result == "# Clean Skill"
            assert "```" not in result

    @pytest.mark.asyncio
    async def it_truncates_result_if_too_long():
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch(
                "skillet.tune.improve.query_assistant_text", new_callable=AsyncMock
            ) as mock_query,
            patch("skillet.tune.improve.MAX_SKILL_LINES", 5),
        ):
            # Return a skill with more lines than allowed
            mock_query.return_value = "line1\nline2\nline3\nline4\nline5\nline6\nline7\nline8"

            skill_path = Path(tmpdir) / "SKILL.md"
            skill_path.write_text("# Short")

            failures = [{"prompt": "p", "expected": "e", "judgment": {"reasoning": "r"}}]
            result = await improve_skill(skill_path, failures)

            lines = result.split("\n")
            assert len(lines) == 5

    @pytest.mark.asyncio
    async def it_handles_skill_directory_input():
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch(
                "skillet.tune.improve.query_assistant_text", new_callable=AsyncMock
            ) as mock_query,
        ):
            mock_query.return_value = "# Result"

            skill_dir = Path(tmpdir)
            (skill_dir / "SKILL.md").write_text("# Directory Skill")

            failures = [{"prompt": "p", "expected": "e", "judgment": {"reasoning": "r"}}]
            result = await improve_skill(skill_dir, failures)

            assert result == "# Result"
            call_args = mock_query.call_args
            prompt = call_args[0][0]
            assert "# Directory Skill" in prompt
