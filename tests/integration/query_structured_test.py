"""Integration tests for query_structured failure modes.

Tests failure modes observed during eval_batch runs where the LLM produces
nondeterministic structured output. These mock the SDK boundary to
deterministically reproduce each failure.

See: notes/eval-batch-failures.md
"""

from collections.abc import AsyncGenerator
from unittest.mock import patch

import pytest
from pydantic import BaseModel

from skillet._internal.sdk.query_structured import query_structured
from skillet.generate.generate import GenerateResponse

from .__fixtures__.query_structured import (
    VALID_CANDIDATES,
    no_structured_output_messages,
    wrapped_structured_output_messages,
)


class SimpleModel(BaseModel):
    data: str


@pytest.mark.no_mirror
def describe_query_structured_failure_modes():
    """Integration tests for SDK failure modes in query_structured."""

    @pytest.fixture(autouse=True)
    def mock_sdk_query():
        """Mock claude_agent_sdk.query with configurable message sequences."""
        messages: list = []

        async def mock_query_gen(**kwargs) -> AsyncGenerator:  # noqa: ARG001
            for msg in messages:
                yield msg

        with patch(
            "skillet._internal.sdk.query_structured.claude_agent_sdk.query",
            mock_query_gen,
        ):
            yield messages

    def describe_no_structured_output():
        """Failure 1: LLM returns only text, no StructuredOutput block."""

        @pytest.mark.asyncio
        async def it_raises_value_error_with_raw_result_text(mock_sdk_query):
            """Current behavior: bare ValueError with no diagnostic info."""
            mock_sdk_query.extend(no_structured_output_messages())

            with pytest.raises(ValueError, match="No structured output"):
                await query_structured("classify this skill", GenerateResponse)

    def describe_wrapped_structured_output():
        """Failure 2: LLM wraps response in extra object key."""

        @pytest.mark.asyncio
        async def it_unwraps_single_key_wrapper_and_validates(mock_sdk_query):
            """After fix: detects {"output": {...}} wrapper and unwraps."""
            mock_sdk_query.extend(wrapped_structured_output_messages())

            result = await query_structured("classify this skill", GenerateResponse)

            assert isinstance(result, GenerateResponse)
            assert len(result.candidates) == 1
            assert result.candidates[0].prompt == VALID_CANDIDATES["candidates"][0]["prompt"]

        @pytest.mark.asyncio
        async def it_falls_through_when_inner_value_is_not_a_dict(mock_sdk_query):
            """Wrapper unwrap only applies when the single value is a dict."""
            from claude_agent_sdk import AssistantMessage, ResultMessage, ToolUseBlock

            mock_sdk_query.extend(
                [
                    AssistantMessage(
                        content=[
                            ToolUseBlock(
                                id="tool-scalar-1",
                                name="StructuredOutput",
                                input={"output": "not a dict"},
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

            # Should still fail validation since {"output": "not a dict"}
            # isn't valid for GenerateResponse and unwrap won't help
            from pydantic import ValidationError

            with pytest.raises(ValidationError):
                await query_structured("classify this", GenerateResponse)

        @pytest.mark.asyncio
        async def it_does_not_unwrap_multi_key_dicts(mock_sdk_query):
            """Wrapper unwrap only applies to single-key dicts."""
            from claude_agent_sdk import AssistantMessage, ResultMessage, ToolUseBlock

            mock_sdk_query.extend(
                [
                    AssistantMessage(
                        content=[
                            ToolUseBlock(
                                id="tool-multi-1",
                                name="StructuredOutput",
                                input={"output": VALID_CANDIDATES, "extra": "key"},
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

            from pydantic import ValidationError

            with pytest.raises(ValidationError):
                await query_structured("classify this", GenerateResponse)
