"""Tests for judge/judge_response module."""

from unittest.mock import AsyncMock, patch

import pytest

from skillet._internal.sdk import StructuredOutputError
from skillet.eval.judge.judge_response import judge_response
from skillet.eval.judge.types import Judgment


def describe_judge_response():
    @pytest.fixture(autouse=True)
    def mock_query_structured():
        with patch(
            "skillet.eval.judge.judge_response.query_structured", new_callable=AsyncMock
        ) as mock:
            mock.return_value = Judgment.model_validate({"pass": True, "reasoning": "OK"})
            yield mock

    @pytest.mark.asyncio
    async def it_returns_pass_true_when_response_passes(mock_query_structured):
        mock_query_structured.return_value = Judgment.model_validate(
            {"pass": True, "reasoning": "Response meets expectations"}
        )

        result = await judge_response(
            prompt="Say hello",
            response="Hello there!",
            expected="A greeting",
        )

        assert result["pass"] is True
        assert "meets expectations" in result["reasoning"]

    @pytest.mark.asyncio
    async def it_returns_pass_false_when_response_fails(mock_query_structured):
        mock_query_structured.return_value = Judgment.model_validate(
            {"pass": False, "reasoning": "Did not greet the user"}
        )

        result = await judge_response(
            prompt="Say hello",
            response="Goodbye",
            expected="A greeting",
        )

        assert result["pass"] is False
        assert "greet" in result["reasoning"]

    @pytest.mark.asyncio
    async def it_includes_tool_calls_in_prompt(mock_query_structured):
        mock_query_structured.return_value = Judgment.model_validate(
            {"pass": True, "reasoning": "Correct tools used"}
        )
        tool_calls = [{"name": "read_file", "input": {"path": "/test.txt"}}]

        await judge_response(
            prompt="Read the file",
            response="File contents",
            expected="Read /test.txt",
            tool_calls=tool_calls,
        )

        call_args = mock_query_structured.call_args
        prompt = call_args[0][0]
        assert "read_file" in prompt
        assert "/test.txt" in prompt

    @pytest.mark.asyncio
    async def it_handles_multi_turn_prompts(mock_query_structured):
        mock_query_structured.return_value = Judgment.model_validate(
            {"pass": True, "reasoning": "Good"}
        )

        await judge_response(
            prompt=["First question", "Follow up"],
            response="Final answer",
            expected="Answer both",
        )

        call_args = mock_query_structured.call_args
        prompt = call_args[0][0]
        assert "Turn 1" in prompt
        assert "Turn 2" in prompt

    @pytest.mark.asyncio
    async def it_handles_missing_reasoning(mock_query_structured):
        mock_query_structured.return_value = Judgment.model_validate({"pass": True})

        result = await judge_response(
            prompt="test",
            response="response",
            expected="expected",
        )

        assert result["pass"] is True
        assert result["reasoning"] == ""

    @pytest.mark.asyncio
    async def it_handles_none_tool_calls(mock_query_structured):
        mock_query_structured.return_value = Judgment.model_validate(
            {"pass": True, "reasoning": "OK"}
        )

        await judge_response(
            prompt="test",
            response="response",
            expected="expected",
            tool_calls=None,
        )

        call_args = mock_query_structured.call_args
        prompt = call_args[0][0]
        assert "(no tools used)" in prompt

    @pytest.mark.asyncio
    async def it_handles_validation_errors(mock_query_structured):
        mock_query_structured.side_effect = ValueError("No structured output returned")

        result = await judge_response(
            prompt="test",
            response="response",
            expected="expected",
        )

        assert result["pass"] is False
        assert "Failed to parse" in result["reasoning"]

    @pytest.mark.asyncio
    async def it_raises_on_backticks_canary(mock_query_structured):
        mock_query_structured.side_effect = StructuredOutputError(
            "Response contains markdown code fences"
        )

        with pytest.raises(StructuredOutputError):
            await judge_response(
                prompt="test",
                response="response",
                expected="expected",
            )

    @pytest.mark.asyncio
    async def it_calls_query_structured_with_judgment_model(mock_query_structured):
        mock_query_structured.return_value = Judgment.model_validate(
            {"pass": True, "reasoning": "OK"}
        )

        await judge_response(
            prompt="test",
            response="response",
            expected="expected",
        )

        call_args = mock_query_structured.call_args
        assert call_args[0][1] is Judgment
        assert call_args[1]["max_turns"] == 1
        assert call_args[1]["allowed_tools"] == []
