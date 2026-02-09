"""Tests for query_multiturn function."""

from unittest.mock import MagicMock, patch

import pytest
from claude_agent_sdk import AssistantMessage, TextBlock, ToolUseBlock

from skillet._internal.sdk.query_multiturn import query_multiturn


def describe_query_multiturn():
    @pytest.mark.asyncio
    async def it_captures_session_id_from_data_dict():
        init_message = MagicMock()
        init_message.subtype = "init"
        init_message.data = {"session_id": "sess-123"}
        del init_message.session_id

        mock_text = MagicMock(spec=TextBlock)
        mock_text.text = "response"
        assistant_message = MagicMock(spec=AssistantMessage)
        assistant_message.content = [mock_text]

        async def mock_query_gen(*_args, **_kwargs):
            yield init_message
            yield assistant_message

        with patch("skillet._internal.sdk.query_multiturn.claude_agent_sdk.query", mock_query_gen):
            result = await query_multiturn(["prompt1"])

            assert result.text == "response"

    @pytest.mark.asyncio
    async def it_handles_init_message_without_session_id():
        init_message = MagicMock()
        init_message.subtype = "init"
        init_message.data = {}  # No session_id
        del init_message.session_id

        mock_text = MagicMock(spec=TextBlock)
        mock_text.text = "response"
        assistant_message = MagicMock(spec=AssistantMessage)
        assistant_message.content = [mock_text]

        async def mock_query_gen(*_args, **_kwargs):
            yield init_message
            yield assistant_message

        with patch("skillet._internal.sdk.query_multiturn.claude_agent_sdk.query", mock_query_gen):
            result = await query_multiturn(["prompt"])

            assert result.text == "response"

    @pytest.mark.asyncio
    async def it_resumes_session_on_subsequent_prompts():
        call_count = 0
        resume_values = []

        async def mock_query_gen(prompt=None, options=None):  # noqa: ARG001
            nonlocal call_count
            call_count += 1
            resume_values.append(getattr(options, "resume", None))

            if call_count == 1:
                init_message = MagicMock()
                init_message.subtype = "init"
                init_message.session_id = "sess-abc"
                yield init_message

            mock_text = MagicMock(spec=TextBlock)
            mock_text.text = f"response {call_count}"
            assistant_message = MagicMock(spec=AssistantMessage)
            assistant_message.content = [mock_text]
            yield assistant_message

        with patch("skillet._internal.sdk.query_multiturn.claude_agent_sdk.query", mock_query_gen):
            result = await query_multiturn(["prompt1", "prompt2"])

            assert len(resume_values) == 2
            assert resume_values[0] is None
            assert resume_values[1] == "sess-abc"
            assert result.text == "response 2"

    @pytest.mark.asyncio
    async def it_collects_tool_calls():
        mock_text = MagicMock(spec=TextBlock)
        mock_text.text = "done"
        mock_tool = MagicMock(spec=ToolUseBlock)
        mock_tool.name = "read_file"
        mock_tool.input = {"path": "/test"}

        assistant_message = MagicMock(spec=AssistantMessage)
        assistant_message.content = [mock_tool, mock_text]

        async def mock_query_gen(*_args, **_kwargs):
            yield assistant_message

        with patch("skillet._internal.sdk.query_multiturn.claude_agent_sdk.query", mock_query_gen):
            result = await query_multiturn(["prompt"])

            assert len(result.tool_calls) == 1
            assert result.tool_calls[0]["name"] == "read_file"
            assert result.tool_calls[0]["input"] == {"path": "/test"}
