"""Tests for eval/run_prompt module."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from skillet._internal.sdk import QueryResult
from skillet.eval.run_prompt import run_prompt


def describe_run_prompt():
    """Tests for run_prompt function."""

    @pytest.mark.asyncio
    async def it_normalizes_string_prompt_to_list():
        with patch("skillet.eval.run_prompt.query_multiturn", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = QueryResult(text="response", tool_calls=[])

            await run_prompt("single prompt")

            mock_query.assert_called_once()
            # First positional arg should be a list
            call_args = mock_query.call_args
            assert call_args[0][0] == ["single prompt"]

    @pytest.mark.asyncio
    async def it_passes_list_prompts_unchanged():
        with patch("skillet.eval.run_prompt.query_multiturn", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = QueryResult(text="response", tool_calls=[])

            await run_prompt(["first", "second"])

            call_args = mock_query.call_args
            assert call_args[0][0] == ["first", "second"]

    @pytest.mark.asyncio
    async def it_sets_cwd_from_skill_path():
        with patch("skillet.eval.run_prompt.query_multiturn", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = QueryResult(text="response", tool_calls=[])

            skill_path = Path("/project/.claude/skills/test")
            await run_prompt("test", skill_path=skill_path)

            call_args = mock_query.call_args
            assert call_args[1]["cwd"] == "/project"

    @pytest.mark.asyncio
    async def it_adds_skill_tool_when_skill_path_provided():
        with patch("skillet.eval.run_prompt.query_multiturn", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = QueryResult(text="response", tool_calls=[])

            skill_path = Path("/project/.claude/skills/test")
            await run_prompt("test", skill_path=skill_path, allowed_tools=["Read"])

            call_args = mock_query.call_args
            assert "Skill" in call_args[1]["allowed_tools"]
            assert "Read" in call_args[1]["allowed_tools"]

    @pytest.mark.asyncio
    async def it_uses_default_tools_when_none_provided():
        with patch("skillet.eval.run_prompt.query_multiturn", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = QueryResult(text="response", tool_calls=[])

            skill_path = Path("/project/.claude/skills/test")
            await run_prompt("test", skill_path=skill_path)

            call_args = mock_query.call_args
            # Should have tools from DEFAULT_SKILL_TOOLS
            assert call_args[1]["allowed_tools"] is not None

    @pytest.mark.asyncio
    async def it_sets_custom_home_dir():
        with (
            patch("skillet.eval.run_prompt.query_multiturn", new_callable=AsyncMock) as mock_query,
            tempfile.TemporaryDirectory() as home_dir,
        ):
            mock_query.return_value = QueryResult(text="response", tool_calls=[])

            await run_prompt("test", home_dir=home_dir)

            call_args = mock_query.call_args
            assert "env" in call_args[1]
            assert call_args[1]["env"]["HOME"] == home_dir

    @pytest.mark.asyncio
    async def it_handles_empty_response():
        with patch("skillet.eval.run_prompt.query_multiturn", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = QueryResult(text="", tool_calls=[])

            result = await run_prompt("test")

            assert "(no text response" in result.text

    @pytest.mark.asyncio
    async def it_does_not_duplicate_skill_tool():
        """Test that Skill is not added if already in allowed_tools."""
        with patch("skillet.eval.run_prompt.query_multiturn", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = QueryResult(text="response", tool_calls=[])

            skill_path = Path("/project/.claude/skills/test")
            # Skill is already in allowed_tools
            await run_prompt("test", skill_path=skill_path, allowed_tools=["Skill", "Read"])

            call_args = mock_query.call_args
            # Should only have one Skill, not duplicated
            assert call_args[1]["allowed_tools"].count("Skill") == 1
            assert call_args[1]["allowed_tools"] == ["Skill", "Read"]

    @pytest.mark.asyncio
    async def it_uses_empty_tools_without_skill():
        """Test that empty tools list is used when no skill and no allowed_tools."""
        with patch("skillet.eval.run_prompt.query_multiturn", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = QueryResult(text="response", tool_calls=[])

            # No skill_path and no allowed_tools
            await run_prompt("test")

            call_args = mock_query.call_args
            # Should be None (no restrictions) since allowed_tools is empty
            assert call_args[1]["allowed_tools"] is None
