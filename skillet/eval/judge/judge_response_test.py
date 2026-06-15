"""Tests for judge/judge_response module."""

from unittest.mock import AsyncMock, patch

import pytest

from skillet.agent import Agent
from skillet.errors import JudgeError
from skillet.eval.judge.judge_response import judge_response
from skillet.eval.judge.types import Judgment


def describe_judge_response():
    @pytest.fixture(autouse=True)
    def mock_judge_via_agent():
        with patch(
            "skillet.eval.judge.judge_response.judge_via_agent", new_callable=AsyncMock
        ) as mock:
            mock.return_value = Judgment.model_validate({"pass": True, "reasoning": "OK"})
            yield mock

    @pytest.mark.asyncio
    async def it_returns_pass_true_when_response_passes(mock_judge_via_agent):
        mock_judge_via_agent.return_value = Judgment.model_validate(
            {"pass": True, "reasoning": "Response meets expectations"}
        )

        result = await judge_response(
            prompt="Say hello",
            response="Hello there!",
            expected="A greeting",
            agent=Agent.CLAUDE,
        )

        assert result["pass"] is True
        assert "meets expectations" in result["reasoning"]

    @pytest.mark.asyncio
    async def it_returns_pass_false_when_response_fails(mock_judge_via_agent):
        mock_judge_via_agent.return_value = Judgment.model_validate(
            {"pass": False, "reasoning": "Did not greet the user"}
        )

        result = await judge_response(
            prompt="Say hello",
            response="Goodbye",
            expected="A greeting",
            agent=Agent.CLAUDE,
        )

        assert result["pass"] is False
        assert "greet" in result["reasoning"]

    @pytest.mark.asyncio
    async def it_routes_through_the_selected_agent(mock_judge_via_agent):
        await judge_response(
            prompt="test",
            response="response",
            expected="expected",
            agent=Agent.CLAUDE,
        )

        assert mock_judge_via_agent.call_args[0][1] is Agent.CLAUDE

    @pytest.mark.asyncio
    async def it_includes_tool_calls_in_prompt(mock_judge_via_agent):
        tool_calls = [{"name": "read_file", "input": {"path": "/test.txt"}}]

        await judge_response(
            prompt="Read the file",
            response="File contents",
            expected="Read /test.txt",
            tool_calls=tool_calls,
            agent=Agent.CLAUDE,
        )

        judge_prompt = mock_judge_via_agent.call_args[0][0]
        assert "read_file" in judge_prompt
        assert "/test.txt" in judge_prompt

    @pytest.mark.asyncio
    async def it_handles_multi_turn_prompts(mock_judge_via_agent):
        await judge_response(
            prompt=["First question", "Follow up"],
            response="Final answer",
            expected="Answer both",
            agent=Agent.CLAUDE,
        )

        judge_prompt = mock_judge_via_agent.call_args[0][0]
        assert "Turn 1" in judge_prompt
        assert "Turn 2" in judge_prompt

    @pytest.mark.asyncio
    async def it_handles_missing_reasoning(mock_judge_via_agent):
        mock_judge_via_agent.return_value = Judgment.model_validate({"pass": True})

        result = await judge_response(
            prompt="test",
            response="response",
            expected="expected",
            agent=Agent.CLAUDE,
        )

        assert result["pass"] is True
        assert result["reasoning"] == ""

    @pytest.mark.asyncio
    async def it_handles_none_tool_calls(mock_judge_via_agent):
        await judge_response(
            prompt="test",
            response="response",
            expected="expected",
            tool_calls=None,
            agent=Agent.CLAUDE,
        )

        judge_prompt = mock_judge_via_agent.call_args[0][0]
        assert "(no tools used)" in judge_prompt

    @pytest.mark.asyncio
    async def it_propagates_judge_errors_loudly(mock_judge_via_agent):
        mock_judge_via_agent.side_effect = JudgeError("no valid verdict")

        with pytest.raises(JudgeError):
            await judge_response(
                prompt="test",
                response="response",
                expected="expected",
                agent=Agent.CLAUDE,
            )
