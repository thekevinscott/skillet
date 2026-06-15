"""Tests for judge/judge_via_agent module."""

from unittest.mock import AsyncMock, patch

import pytest

from skillet._internal.sdk import QueryResult
from skillet.agent import Agent
from skillet.errors import JudgeError
from skillet.eval.judge.judge_via_agent import judge_via_agent
from skillet.eval.judge.types import Judgment


def describe_judge_via_agent():
    @pytest.fixture(autouse=True)
    def mock_run_agent():
        with patch("skillet.eval.judge.judge_via_agent.run_agent", new_callable=AsyncMock) as mock:
            mock.return_value = QueryResult(text='{"pass": true}', tool_calls=[])
            yield mock

    @pytest.fixture(autouse=True)
    def mock_parse_judgment():
        with patch("skillet.eval.judge.judge_via_agent.parse_judgment") as mock:
            mock.return_value = Judgment.model_validate({"pass": True, "reasoning": "OK"})
            yield mock

    @pytest.mark.asyncio
    async def it_returns_parsed_judgment_on_first_success(mock_run_agent, mock_parse_judgment):
        result = await judge_via_agent("judge this", Agent.CLAUDE)

        assert result.passed is True
        assert result.reasoning == "OK"
        assert mock_run_agent.call_count == 1
        assert mock_parse_judgment.call_count == 1

    @pytest.mark.asyncio
    async def it_runs_the_prompt_through_the_selected_agent(mock_run_agent):
        await judge_via_agent("judge this", Agent.CLAUDE)

        call = mock_run_agent.call_args
        assert call[0][0] is Agent.CLAUDE
        assert call[0][1] == ["judge this"]

    @pytest.mark.asyncio
    async def it_judges_with_no_tools_allowed(mock_run_agent):
        await judge_via_agent("judge this", Agent.CLAUDE)

        assert mock_run_agent.call_args[1]["allowed_tools"] == []

    @pytest.mark.asyncio
    async def it_retries_once_on_invalid_json(mock_run_agent, mock_parse_judgment):
        mock_parse_judgment.side_effect = [
            ValueError("not valid JSON"),
            Judgment.model_validate({"pass": False, "reasoning": "Recovered"}),
        ]

        result = await judge_via_agent("judge this", Agent.CLAUDE)

        assert result.passed is False
        assert result.reasoning == "Recovered"
        assert mock_run_agent.call_count == 2

    @pytest.mark.asyncio
    async def it_uses_a_stricter_prompt_on_retry(mock_run_agent, mock_parse_judgment):
        mock_parse_judgment.side_effect = [
            ValueError("not valid JSON"),
            Judgment.model_validate({"pass": True, "reasoning": "OK"}),
        ]

        await judge_via_agent("judge this", Agent.CLAUDE)

        first_prompt = mock_run_agent.call_args_list[0][0][1][0]
        retry_prompt = mock_run_agent.call_args_list[1][0][1][0]
        assert first_prompt == "judge this"
        assert retry_prompt != first_prompt
        assert "JSON" in retry_prompt

    @pytest.mark.asyncio
    async def it_raises_judge_error_after_two_invalid_replies(mock_run_agent, mock_parse_judgment):
        mock_parse_judgment.side_effect = [
            ValueError("bad once"),
            ValueError("bad twice"),
        ]

        with pytest.raises(JudgeError, match="valid verdict"):
            await judge_via_agent("judge this", Agent.CLAUDE)

        assert mock_run_agent.call_count == 2

    @pytest.mark.asyncio
    async def it_does_not_retry_when_the_agent_cli_errors(mock_run_agent):
        mock_run_agent.side_effect = RuntimeError("claude exited non-zero")

        with pytest.raises(RuntimeError, match="exited non-zero"):
            await judge_via_agent("judge this", Agent.CLAUDE)

        assert mock_run_agent.call_count == 1
