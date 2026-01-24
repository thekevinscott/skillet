"""Tests for eval/judge module."""

from unittest.mock import AsyncMock, patch

import pytest

from skillet._internal.sdk import StructuredOutputError
from skillet.eval.judge import (
    Judgment,
    format_prompt_for_judge,
    format_tool_calls_for_judge,
    judge_response,
)


def describe_format_prompt_for_judge():
    """Tests for format_prompt_for_judge function."""

    def it_returns_string_prompt_unchanged():
        result = format_prompt_for_judge("simple prompt")
        assert result == "simple prompt"

    def it_formats_multi_turn_prompts():
        prompts = ["first message", "second message", "third message"]
        result = format_prompt_for_judge(prompts)
        assert "Turn 1: first message" in result
        assert "Turn 2: second message" in result
        assert "Turn 3: third message" in result

    def it_handles_single_item_list():
        result = format_prompt_for_judge(["only one"])
        assert result == "Turn 1: only one"


def describe_format_tool_calls_for_judge():
    """Tests for format_tool_calls_for_judge function."""

    def it_returns_no_tools_message_for_empty_list():
        result = format_tool_calls_for_judge([])
        assert result == "(no tools used)"

    def it_formats_single_tool_call():
        tool_calls = [{"name": "read_file", "input": {"path": "/test.txt"}}]
        result = format_tool_calls_for_judge(tool_calls)
        assert "read_file" in result
        assert "/test.txt" in result

    def it_formats_multiple_tool_calls():
        tool_calls = [
            {"name": "read_file", "input": {"path": "/a.txt"}},
            {"name": "write_file", "input": {"path": "/b.txt", "content": "hello"}},
        ]
        result = format_tool_calls_for_judge(tool_calls)
        assert "read_file" in result
        assert "write_file" in result
        assert "/a.txt" in result
        assert "/b.txt" in result

    def it_handles_empty_input():
        tool_calls = [{"name": "some_tool", "input": {}}]
        result = format_tool_calls_for_judge(tool_calls)
        assert "some_tool" in result

    def it_handles_missing_input_key():
        tool_calls = [{"name": "some_tool"}]
        result = format_tool_calls_for_judge(tool_calls)
        assert "some_tool" in result


def describe_judge_response():
    """Tests for judge_response function."""

    @pytest.fixture(autouse=True)
    def mock_query_structured():
        """Mock query_structured for all tests in this describe block."""
        with patch("skillet.eval.judge.query_structured", new_callable=AsyncMock) as mock:
            # Default return value - use model_validate with alias for type safety
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
        """Test that StructuredOutputError is raised if backticks detected."""
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
