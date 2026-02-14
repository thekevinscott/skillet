"""Tests for query_structured and StructuredOutputError."""

from unittest.mock import MagicMock, patch

import pytest
from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock, ToolUseBlock
from pydantic import BaseModel, ValidationError

from skillet._internal.sdk.query_structured import (
    StructuredOutputError,
    _validate_with_unwrap,
    query_structured,
)


class MockQuery:
    """Helper class for mock query fixtures."""

    def __init__(self):
        self.messages: list = []
        self.captured: dict = {"options": None}
        self.fully_consumed: bool = False


def describe_StructuredOutputError():
    def it_can_be_raised_with_message():
        with pytest.raises(StructuredOutputError) as exc_info:
            raise StructuredOutputError("test message")
        assert "test message" in str(exc_info.value)

    def it_is_an_exception():
        assert issubclass(StructuredOutputError, Exception)


def describe_validate_with_unwrap():
    class Inner(BaseModel):
        value: int

    def it_validates_direct_match():
        result = _validate_with_unwrap(Inner, {"value": 42})
        assert result.value == 42

    def it_unwraps_single_key_dict_on_failure():
        result = _validate_with_unwrap(Inner, {"output": {"value": 42}})
        assert result.value == 42

    def it_unwraps_any_single_key_name():
        result = _validate_with_unwrap(Inner, {"result": {"value": 42}})
        assert result.value == 42

    def it_raises_when_inner_also_fails_validation():
        with pytest.raises(ValidationError):
            _validate_with_unwrap(Inner, {"output": {"wrong_field": 42}})

    def it_raises_for_multi_key_dict():
        with pytest.raises(ValidationError):
            _validate_with_unwrap(Inner, {"output": {"value": 42}, "extra": "key"})

    def it_raises_when_inner_value_is_not_dict():
        with pytest.raises(ValidationError):
            _validate_with_unwrap(Inner, {"output": "not a dict"})

    def it_raises_for_completely_invalid_data():
        with pytest.raises(ValidationError):
            _validate_with_unwrap(Inner, {"wrong": "data"})


def describe_query_structured():
    @pytest.fixture(autouse=True)
    def mock_query():
        """Mock claude_agent_sdk.query for all tests in this block."""
        state = MockQuery()

        async def mock_query_gen(prompt=None, options=None):  # noqa: ARG001
            state.captured["options"] = options
            for msg in state.messages:
                yield msg

        with patch("skillet._internal.sdk.query_structured.claude_agent_sdk.query", mock_query_gen):
            yield state

    @pytest.mark.asyncio
    async def it_extracts_structured_output_from_tool_use_block(mock_query):
        class TestModel(BaseModel):
            name: str
            value: int

        mock_query.messages.append(
            AssistantMessage(
                content=[
                    ToolUseBlock(
                        id="tool-1",
                        name="StructuredOutput",
                        input={"name": "test", "value": 42},
                    )
                ],
                model="claude-sonnet-4-20250514",
            )
        )

        result = await query_structured("test prompt", TestModel)

        assert isinstance(result, TestModel)
        assert result.name == "test"
        assert result.value == 42

    @pytest.mark.asyncio
    async def it_falls_back_to_result_message_structured_output(mock_query):
        """ResultMessage.structured_output fallback for forward compatibility."""

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
        class TestModel(BaseModel):
            data: str

        mock_query.messages.append(
            AssistantMessage(
                content=[
                    ToolUseBlock(id="tool-1", name="StructuredOutput", input={"data": "test"})
                ],
                model="claude-sonnet-4-20250514",
            )
        )

        await query_structured("test", TestModel)

        assert mock_query.captured["options"] is not None
        assert mock_query.captured["options"].output_format["type"] == "json_schema"
        assert "schema" in mock_query.captured["options"].output_format

    @pytest.mark.asyncio
    async def it_raises_on_backticks_in_result(mock_query):
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
        class NotPydantic:
            pass

        with pytest.raises(TypeError) as exc_info:
            await query_structured("test", NotPydantic)  # type: ignore[type-var]

        assert "Pydantic BaseModel" in str(exc_info.value)

    @pytest.mark.asyncio
    async def it_passes_through_additional_options(mock_query):
        class TestModel(BaseModel):
            data: str

        mock_query.messages.append(
            AssistantMessage(
                content=[
                    ToolUseBlock(id="tool-1", name="StructuredOutput", input={"data": "test"})
                ],
                model="claude-sonnet-4-20250514",
            )
        )

        await query_structured("test", TestModel, max_turns=5, allowed_tools=["Read"])

        assert mock_query.captured["options"] is not None
        assert mock_query.captured["options"].max_turns == 5
        assert mock_query.captured["options"].allowed_tools == ["Read"]


def describe_generator_consumption():
    """Verify query_structured fully consumes the SDK async generator.

    Abandoning the generator (via early return/break from async for) defers
    cleanup to GC, which may run in a different asyncio.Task -- triggering
    RuntimeError from anyio's CancelScope. See SDK issues #378, #454.
    """

    @pytest.fixture(autouse=True)
    def mock_query():
        state = MockQuery()
        state.fully_consumed = False

        async def mock_query_gen(prompt=None, options=None):  # noqa: ARG001
            state.captured["options"] = options
            for msg in state.messages:
                yield msg
            state.fully_consumed = True

        with patch(
            "skillet._internal.sdk.query_structured.claude_agent_sdk.query",
            mock_query_gen,
        ):
            yield state

    @pytest.mark.asyncio
    async def it_consumes_all_messages_after_finding_structured_output(mock_query):
        class TestModel(BaseModel):
            name: str
            value: int

        mock_query.messages.extend(
            [
                AssistantMessage(
                    content=[
                        ToolUseBlock(
                            id="tool-1",
                            name="StructuredOutput",
                            input={"name": "test", "value": 42},
                        )
                    ],
                    model="claude-sonnet-4-20250514",
                ),
                ResultMessage(
                    subtype="result",
                    duration_ms=100,
                    duration_api_ms=100,
                    is_error=False,
                    num_turns=1,
                    session_id="mock-session",
                    result=None,
                    structured_output=None,
                ),
            ]
        )

        result = await query_structured("test prompt", TestModel)

        assert isinstance(result, TestModel)
        assert result.name == "test"
        assert mock_query.fully_consumed, (
            "SDK generator was not fully consumed. "
            "Early return from async for abandons the generator, causing "
            "RuntimeError in anyio cancel scopes under parallel execution."
        )

    @pytest.mark.asyncio
    async def it_consumes_generator_even_when_backtick_canary_triggers(mock_query):
        """StructuredOutputError must not abandon the generator.

        Raising inside `async for` breaks the loop, deferring generator cleanup
        to GC -- which runs in a different asyncio.Task and triggers RuntimeError
        from anyio's CancelScope.
        """

        class TestModel(BaseModel):
            data: str

        mock_result = MagicMock(spec=ResultMessage)
        mock_result.structured_output = None
        mock_result.result = '```json\n{"data": "test"}\n```'
        mock_query.messages.extend(
            [
                mock_result,
                # Extra message after the error-triggering one
                AssistantMessage(
                    content=[TextBlock(text="trailing")],
                    model="claude-sonnet-4-20250514",
                ),
            ]
        )

        with pytest.raises(StructuredOutputError):
            await query_structured("test", TestModel)

        assert mock_query.fully_consumed, (
            "SDK generator was not fully consumed after StructuredOutputError. "
            "Raising inside async for abandons the generator, causing "
            "RuntimeError in anyio cancel scopes."
        )

    @pytest.mark.asyncio
    async def it_consumes_generator_even_when_validation_fails(mock_query):
        """ValidationError must not abandon the generator."""

        class StrictModel(BaseModel):
            required_field: int

        mock_query.messages.extend(
            [
                AssistantMessage(
                    content=[
                        ToolUseBlock(
                            id="tool-1",
                            name="StructuredOutput",
                            input={"wrong_field": "not_an_int"},
                        )
                    ],
                    model="claude-sonnet-4-20250514",
                ),
                ResultMessage(
                    subtype="result",
                    duration_ms=100,
                    duration_api_ms=100,
                    is_error=False,
                    num_turns=1,
                    session_id="mock-session",
                    result=None,
                    structured_output=None,
                ),
            ]
        )

        with pytest.raises(ValidationError):
            await query_structured("test", StrictModel)

        assert mock_query.fully_consumed, (
            "SDK generator was not fully consumed after ValidationError. "
            "Raising inside async for abandons the generator, causing "
            "RuntimeError in anyio cancel scopes."
        )
