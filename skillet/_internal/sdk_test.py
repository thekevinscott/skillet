"""Tests for sdk module."""

from unittest.mock import MagicMock, patch

import pytest

from skillet._internal.sdk import (
    QueryResult,
    _stderr_callback,
    for_query,
    query_assistant_text,
    query_multiturn,
)


def describe_QueryResult():
    """Tests for QueryResult dataclass."""

    def it_creates_with_text_only():
        result = QueryResult(text="hello world")
        assert result.text == "hello world"
        assert result.tool_calls == []

    def it_creates_with_text_and_tool_calls():
        tool_calls = [{"name": "read_file", "input": {"path": "/test"}}]
        result = QueryResult(text="response", tool_calls=tool_calls)
        assert result.text == "response"
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0]["name"] == "read_file"

    def it_has_empty_tool_calls_by_default():
        result = QueryResult(text="test")
        assert result.tool_calls == []
        # Verify it's a new list each time (not shared)
        result.tool_calls.append({"name": "test"})
        result2 = QueryResult(text="test2")
        assert result2.tool_calls == []

    def it_can_have_multiple_tool_calls():
        tool_calls = [
            {"name": "read_file", "input": {"path": "/a"}},
            {"name": "write_file", "input": {"path": "/b", "content": "test"}},
            {"name": "bash", "input": {"command": "ls"}},
        ]
        result = QueryResult(text="done", tool_calls=tool_calls)
        assert len(result.tool_calls) == 3


def describe_stderr_callback():
    """Tests for _stderr_callback function."""

    def it_prints_to_stderr(capsys):
        _stderr_callback("test message")
        captured = capsys.readouterr()
        assert "test message" in captured.err

    def it_handles_empty_string(capsys):
        _stderr_callback("")
        captured = capsys.readouterr()
        assert captured.err == "\n"


def describe_for_query():
    """Tests for for_query async generator."""

    @pytest.mark.asyncio
    async def it_yields_blocks_from_messages():
        """Test that for_query yields content blocks from messages."""
        # Create mock message with content
        mock_block = MagicMock()
        mock_block.text = "hello"
        mock_message = MagicMock()
        mock_message.content = [mock_block]

        async def mock_query_gen(*_args, **_kwargs):
            yield mock_message

        with patch("skillet._internal.sdk.query", mock_query_gen):
            blocks = []
            async for block in for_query("test prompt"):
                blocks.append(block)

            assert len(blocks) == 1
            assert blocks[0].text == "hello"

    @pytest.mark.asyncio
    async def it_filters_by_block_type():
        """Test that block_type parameter filters blocks."""
        from claude_agent_sdk import TextBlock, ToolUseBlock

        # Create mock text block
        mock_text_block = MagicMock(spec=TextBlock)
        mock_text_block.text = "text content"

        # Create mock tool use block
        mock_tool_block = MagicMock(spec=ToolUseBlock)
        mock_tool_block.name = "bash"

        mock_message = MagicMock()
        mock_message.content = [mock_text_block, mock_tool_block]

        async def mock_query_gen(*_args, **_kwargs):
            yield mock_message

        with patch("skillet._internal.sdk.query", mock_query_gen):
            # Filter to only TextBlock
            blocks = []
            async for block in for_query("test", block_type=TextBlock):
                blocks.append(block)

            assert len(blocks) == 1
            assert blocks[0].text == "text content"

    @pytest.mark.asyncio
    async def it_skips_messages_without_content():
        """Test that messages without content attribute are skipped."""
        mock_message = MagicMock(spec=[])  # No content attribute
        del mock_message.content  # Ensure no content attr

        async def mock_query_gen(*_args, **_kwargs):
            yield mock_message

        with patch("skillet._internal.sdk.query", mock_query_gen):
            blocks = []
            async for block in for_query("test"):
                blocks.append(block)

            assert len(blocks) == 0


def describe_query_assistant_text():
    """Tests for query_assistant_text function."""

    @pytest.mark.asyncio
    async def it_returns_concatenated_text():
        """Test that text blocks are concatenated."""
        from claude_agent_sdk import AssistantMessage, TextBlock

        mock_text1 = MagicMock(spec=TextBlock)
        mock_text1.text = "Hello "
        mock_text2 = MagicMock(spec=TextBlock)
        mock_text2.text = "World"

        mock_message = MagicMock(spec=AssistantMessage)
        mock_message.content = [mock_text1, mock_text2]

        async def mock_query_gen(*_args, **_kwargs):
            yield mock_message

        with patch("skillet._internal.sdk.query", mock_query_gen):
            result = await query_assistant_text("test prompt")

            assert result == "Hello World"

    @pytest.mark.asyncio
    async def it_strips_whitespace():
        """Test that result is stripped."""
        from claude_agent_sdk import AssistantMessage, TextBlock

        mock_text = MagicMock(spec=TextBlock)
        mock_text.text = "  response  "

        mock_message = MagicMock(spec=AssistantMessage)
        mock_message.content = [mock_text]

        async def mock_query_gen(*_args, **_kwargs):
            yield mock_message

        with patch("skillet._internal.sdk.query", mock_query_gen):
            result = await query_assistant_text("test")

            assert result == "response"


def describe_query_multiturn():
    """Tests for query_multiturn function."""

    @pytest.mark.asyncio
    async def it_captures_session_id_from_data_dict():
        """Test session_id extraction from data dict."""
        from claude_agent_sdk import AssistantMessage, TextBlock

        # Create init message with session_id in data dict
        init_message = MagicMock()
        init_message.subtype = "init"
        init_message.data = {"session_id": "sess-123"}
        # Remove session_id attribute to force data dict path
        del init_message.session_id

        # Create assistant message
        mock_text = MagicMock(spec=TextBlock)
        mock_text.text = "response"
        assistant_message = MagicMock(spec=AssistantMessage)
        assistant_message.content = [mock_text]

        async def mock_query_gen(*_args, **_kwargs):
            yield init_message
            yield assistant_message

        with patch("skillet._internal.sdk.query", mock_query_gen):
            result = await query_multiturn(["prompt1"])

            assert result.text == "response"

    @pytest.mark.asyncio
    async def it_handles_init_message_without_session_id():
        """Test handling of init message with no session_id."""
        from claude_agent_sdk import AssistantMessage, TextBlock

        # Create init message without session_id
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

        with patch("skillet._internal.sdk.query", mock_query_gen):
            result = await query_multiturn(["prompt"])

            assert result.text == "response"

    @pytest.mark.asyncio
    async def it_resumes_session_on_subsequent_prompts():
        """Test that session is resumed for multi-turn conversations."""
        from claude_agent_sdk import AssistantMessage, TextBlock

        call_count = 0
        resume_values = []

        async def mock_query_gen(prompt=None, options=None):  # noqa: ARG001
            nonlocal call_count
            call_count += 1
            # Capture the resume value at the time of call
            resume_values.append(getattr(options, "resume", None))

            # First call: init message with session_id
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

        with patch("skillet._internal.sdk.query", mock_query_gen):
            result = await query_multiturn(["prompt1", "prompt2"])

            # First call should not have resume, second should
            assert len(resume_values) == 2
            assert resume_values[0] is None
            assert resume_values[1] == "sess-abc"
            # Result should be from last prompt
            assert result.text == "response 2"

    @pytest.mark.asyncio
    async def it_collects_tool_calls():
        """Test that tool calls are collected across messages."""
        from claude_agent_sdk import AssistantMessage, TextBlock, ToolUseBlock

        mock_text = MagicMock(spec=TextBlock)
        mock_text.text = "done"
        mock_tool = MagicMock(spec=ToolUseBlock)
        mock_tool.name = "read_file"
        mock_tool.input = {"path": "/test"}

        assistant_message = MagicMock(spec=AssistantMessage)
        assistant_message.content = [mock_tool, mock_text]

        async def mock_query_gen(*_args, **_kwargs):
            yield assistant_message

        with patch("skillet._internal.sdk.query", mock_query_gen):
            result = await query_multiturn(["prompt"])

            assert len(result.tool_calls) == 1
            assert result.tool_calls[0]["name"] == "read_file"
            assert result.tool_calls[0]["input"] == {"path": "/test"}
