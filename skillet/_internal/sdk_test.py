"""Tests for sdk module."""

from unittest.mock import MagicMock, patch

import pytest

from skillet._internal.sdk import (
    QueryResult,
    StructuredOutputError,
    _stderr_callback,
    query_multiturn,
    query_structured,
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


def describe_query_multiturn():
    """Tests for query_multiturn function."""

    @pytest.mark.asyncio
    async def it_captures_session_id_from_data_dict():
        """Test session_id extraction from data dict."""
        from claude_agent_sdk import AssistantMessage, TextBlock

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

        with patch("claude_agent_sdk.query", mock_query_gen):
            result = await query_multiturn(["prompt1"])

            assert result.text == "response"

    @pytest.mark.asyncio
    async def it_handles_init_message_without_session_id():
        """Test handling of init message with no session_id."""
        from claude_agent_sdk import AssistantMessage, TextBlock

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

        with patch("claude_agent_sdk.query", mock_query_gen):
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

        with patch("claude_agent_sdk.query", mock_query_gen):
            result = await query_multiturn(["prompt1", "prompt2"])

            assert len(resume_values) == 2
            assert resume_values[0] is None
            assert resume_values[1] == "sess-abc"
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

        with patch("claude_agent_sdk.query", mock_query_gen):
            result = await query_multiturn(["prompt"])

            assert len(result.tool_calls) == 1
            assert result.tool_calls[0]["name"] == "read_file"
            assert result.tool_calls[0]["input"] == {"path": "/test"}


def describe_StructuredOutputError():
    """Tests for StructuredOutputError exception."""

    def it_can_be_raised_with_message():
        with pytest.raises(StructuredOutputError) as exc_info:
            raise StructuredOutputError("test message")
        assert "test message" in str(exc_info.value)

    def it_is_an_exception():
        assert issubclass(StructuredOutputError, Exception)


class MockQuery:
    """Helper class for mock query fixtures."""

    def __init__(self):
        self.messages: list = []
        self.captured: dict = {"options": None}


def describe_query_structured():
    """Tests for query_structured function."""

    @pytest.fixture(autouse=True)
    def mock_query():
        """Mock claude_agent_sdk.query for all tests in this block."""
        state = MockQuery()

        async def mock_query_gen(prompt=None, options=None):  # noqa: ARG001
            state.captured["options"] = options
            for msg in state.messages:
                yield msg

        with patch("claude_agent_sdk.query", mock_query_gen):
            yield state

    @pytest.mark.asyncio
    async def it_returns_validated_pydantic_model(mock_query):
        """Test that structured output is validated into a Pydantic model."""
        from claude_agent_sdk import ResultMessage
        from pydantic import BaseModel

        class TestModel(BaseModel):
            name: str
            value: int

        mock_result = MagicMock(spec=ResultMessage)
        mock_result.structured_output = {"name": "test", "value": 42}
        mock_result.result = None
        mock_query.messages.append(mock_result)

        result = await query_structured("test prompt", TestModel)

        assert isinstance(result, TestModel)
        assert result.name == "test"
        assert result.value == 42

    @pytest.mark.asyncio
    async def it_passes_json_schema_output_format(mock_query):
        """Test that output_format with json_schema type is passed."""
        from claude_agent_sdk import ResultMessage
        from pydantic import BaseModel

        class TestModel(BaseModel):
            data: str

        mock_result = MagicMock(spec=ResultMessage)
        mock_result.structured_output = {"data": "test"}
        mock_result.result = None
        mock_query.messages.append(mock_result)

        await query_structured("test", TestModel)

        assert mock_query.captured["options"] is not None
        assert mock_query.captured["options"].output_format["type"] == "json_schema"
        assert "schema" in mock_query.captured["options"].output_format

    @pytest.mark.asyncio
    async def it_raises_on_backticks_in_result(mock_query):
        """Test that StructuredOutputError is raised when backticks detected."""
        from claude_agent_sdk import ResultMessage
        from pydantic import BaseModel

        class TestModel(BaseModel):
            data: str

        mock_result = MagicMock(spec=ResultMessage)
        mock_result.structured_output = None
        mock_result.result = '```json\n{"data": "test"}\n```'
        mock_query.messages.append(mock_result)

        with pytest.raises(StructuredOutputError) as exc_info:
            await query_structured("test", TestModel)

        assert "markdown code fences" in str(exc_info.value)

    @pytest.mark.asyncio
    async def it_raises_value_error_when_no_structured_output(mock_query):
        """Test that ValueError is raised when no structured output returned."""
        from claude_agent_sdk import AssistantMessage, TextBlock
        from pydantic import BaseModel

        class TestModel(BaseModel):
            data: str

        mock_text = MagicMock(spec=TextBlock)
        mock_text.text = "plain text"
        mock_message = MagicMock(spec=AssistantMessage)
        mock_message.content = [mock_text]
        mock_query.messages.append(mock_message)

        with pytest.raises(ValueError) as exc_info:
            await query_structured("test", TestModel)

        assert "No structured output" in str(exc_info.value)

    @pytest.mark.asyncio
    async def it_raises_type_error_for_non_pydantic_model():
        """Test that TypeError is raised if model is not a Pydantic BaseModel."""

        class NotPydantic:
            pass

        with pytest.raises(TypeError) as exc_info:
            await query_structured("test", NotPydantic)  # type: ignore[type-var]

        assert "Pydantic BaseModel" in str(exc_info.value)

    @pytest.mark.asyncio
    async def it_passes_through_additional_options(mock_query):
        """Test that additional options are passed to ClaudeAgentOptions."""
        from claude_agent_sdk import ResultMessage
        from pydantic import BaseModel

        class TestModel(BaseModel):
            data: str

        mock_result = MagicMock(spec=ResultMessage)
        mock_result.structured_output = {"data": "test"}
        mock_result.result = None
        mock_query.messages.append(mock_result)

        await query_structured("test", TestModel, max_turns=5, allowed_tools=["Read"])

        assert mock_query.captured["options"] is not None
        assert mock_query.captured["options"].max_turns == 5
        assert mock_query.captured["options"].allowed_tools == ["Read"]
