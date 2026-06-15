"""Tests for eval/run_prompt module."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from skillet._internal.sdk import QueryResult
from skillet.agent import Agent
from skillet.eval.run_prompt import run_prompt


def describe_run_prompt():
    """Tests for run_prompt function."""

    @pytest.mark.asyncio
    async def it_normalizes_string_prompt_to_list():
        with patch("skillet.eval.run_prompt.run_agent", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = QueryResult(text="response", tool_calls=[])

            await run_prompt("single prompt", agent=Agent.CLAUDE)

            mock_run.assert_called_once()
            call_args = mock_run.call_args
            # First positional arg is the agent, second is the prompt list
            assert call_args[0][0] is Agent.CLAUDE
            assert call_args[0][1] == ["single prompt"]

    @pytest.mark.asyncio
    async def it_passes_list_prompts_unchanged():
        with patch("skillet.eval.run_prompt.run_agent", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = QueryResult(text="response", tool_calls=[])

            await run_prompt(["first", "second"], agent=Agent.CLAUDE)

            call_args = mock_run.call_args
            assert call_args[0][1] == ["first", "second"]

    @pytest.mark.asyncio
    async def it_sets_cwd_from_skill_path():
        with patch("skillet.eval.run_prompt.run_agent", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = QueryResult(text="response", tool_calls=[])

            skill_path = Path("/project/.claude/skills/test")
            await run_prompt("test", skill_path=skill_path, agent=Agent.CLAUDE)

            call_args = mock_run.call_args
            assert call_args[1]["cwd"] == "/project"

    @pytest.mark.asyncio
    async def it_adds_skill_tool_when_skill_path_provided():
        with patch("skillet.eval.run_prompt.run_agent", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = QueryResult(text="response", tool_calls=[])

            skill_path = Path("/project/.claude/skills/test")
            await run_prompt(
                "test", skill_path=skill_path, allowed_tools=["Read"], agent=Agent.CLAUDE
            )

            call_args = mock_run.call_args
            assert "Skill" in call_args[1]["allowed_tools"]
            assert "Read" in call_args[1]["allowed_tools"]

    @pytest.mark.asyncio
    async def it_uses_default_tools_when_none_provided():
        with patch("skillet.eval.run_prompt.run_agent", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = QueryResult(text="response", tool_calls=[])

            skill_path = Path("/project/.claude/skills/test")
            await run_prompt("test", skill_path=skill_path, agent=Agent.CLAUDE)

            call_args = mock_run.call_args
            # Should have tools from DEFAULT_SKILL_TOOLS
            assert call_args[1]["allowed_tools"] is not None

    @pytest.mark.asyncio
    async def it_passes_agent_through():
        with patch("skillet.eval.run_prompt.run_agent", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = QueryResult(text="response", tool_calls=[])

            await run_prompt("test", agent=Agent.CODEX)

            assert mock_run.call_args[0][0] is Agent.CODEX

    @pytest.mark.asyncio
    async def it_sets_custom_home_dir():
        with (
            patch("skillet.eval.run_prompt.run_agent", new_callable=AsyncMock) as mock_run,
            tempfile.TemporaryDirectory() as home_dir,
        ):
            mock_run.return_value = QueryResult(text="response", tool_calls=[])

            await run_prompt("test", home_dir=home_dir, agent=Agent.CLAUDE)

            call_args = mock_run.call_args
            assert call_args[1]["env"] is not None
            assert call_args[1]["env"]["HOME"] == home_dir

    @pytest.mark.asyncio
    async def it_handles_empty_response():
        with patch("skillet.eval.run_prompt.run_agent", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = QueryResult(text="", tool_calls=[])

            result = await run_prompt("test", agent=Agent.CLAUDE)

            assert "(no text response" in result.text

    @pytest.mark.asyncio
    async def it_does_not_duplicate_skill_tool():
        """Test that Skill is not added if already in allowed_tools."""
        with patch("skillet.eval.run_prompt.run_agent", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = QueryResult(text="response", tool_calls=[])

            skill_path = Path("/project/.claude/skills/test")
            # Skill is already in allowed_tools
            await run_prompt(
                "test", skill_path=skill_path, allowed_tools=["Skill", "Read"], agent=Agent.CLAUDE
            )

            call_args = mock_run.call_args
            # Should only have one Skill, not duplicated
            assert call_args[1]["allowed_tools"].count("Skill") == 1
            assert call_args[1]["allowed_tools"] == ["Skill", "Read"]

    @pytest.mark.asyncio
    async def it_uses_empty_tools_without_skill():
        """Test that empty tools list is used when no skill and no allowed_tools."""
        with patch("skillet.eval.run_prompt.run_agent", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = QueryResult(text="response", tool_calls=[])

            # No skill_path and no allowed_tools
            await run_prompt("test", agent=Agent.CLAUDE)

            call_args = mock_run.call_args
            # Should be None (no restrictions) since allowed_tools is empty
            assert call_args[1]["allowed_tools"] is None
