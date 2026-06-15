"""Tests for run_agent dispatch."""

from unittest.mock import AsyncMock, patch

import pytest

from skillet._internal.agent.run_agent import run_agent
from skillet._internal.sdk.query_result import QueryResult
from skillet.agent import Agent


def describe_run_agent():
    """Tests for dispatching to the selected agent's CLI runner."""

    @pytest.mark.asyncio
    async def it_dispatches_claude_to_run_claude_cli():
        expected = QueryResult(text="hi", tool_calls=[])
        runner = AsyncMock(return_value=expected)

        with patch("skillet._internal.agent.run_agent.run_claude_cli", runner):
            result = await run_agent(
                Agent.CLAUDE, ["prompt"], allowed_tools=["Skill"], cwd="/s", env={"HOME": "/h"}
            )

        assert result is expected
        runner.assert_awaited_once_with(
            ["prompt"], allowed_tools=["Skill"], cwd="/s", env={"HOME": "/h"}
        )

    @pytest.mark.asyncio
    async def it_raises_not_implemented_for_codex():
        with pytest.raises(NotImplementedError, match=r"codex.*not yet supported"):
            await run_agent(Agent.CODEX, ["prompt"])
