"""Integration tests for query_structured failure modes.

Tests failure modes observed during eval_batch runs where the LLM produces
nondeterministic structured output. These mock the SDK boundary to
deterministically reproduce each failure.

See: notes/eval-batch-failures.md
"""

import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import patch

import pytest
from claude_agent_sdk import AssistantMessage, ResultMessage, ToolUseBlock
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


@pytest.mark.no_mirror
def describe_generator_consumption():
    """Verify query_structured fully consumes SDK generator under parallel execution.

    When multiple query_structured calls run via asyncio.gather (as in evaluate()),
    abandoning async generators causes anyio cancel scope errors. This tests the
    real composition: judge_response -> query_structured -> SDK mock.
    """

    @pytest.fixture(autouse=True)
    def mock_sdk_query():
        call_count = {"total": 0, "fully_consumed": 0}

        async def mock_query_gen(**kwargs) -> AsyncGenerator:  # noqa: ARG001
            call_count["total"] += 1
            for msg in [
                AssistantMessage(
                    content=[
                        ToolUseBlock(
                            id="tool-1",
                            name="StructuredOutput",
                            input={"pass": True, "reasoning": "meets expectations"},
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
            ]:
                yield msg
            call_count["fully_consumed"] += 1

        with patch(
            "skillet._internal.sdk.query_structured.claude_agent_sdk.query",
            mock_query_gen,
        ):
            yield call_count

    @pytest.mark.asyncio
    async def it_consumes_all_generators_under_parallel_gather(mock_sdk_query):
        """Multiple parallel judge_response calls must all fully consume generators."""
        from skillet.eval.judge import judge_response

        tasks = [
            judge_response(
                prompt=f"test prompt {i}",
                response=f"test response {i}",
                expected="expected behavior",
            )
            for i in range(5)
        ]

        results = await asyncio.gather(*tasks)

        assert all(r["pass"] for r in results)
        assert mock_sdk_query["total"] == 5
        assert mock_sdk_query["fully_consumed"] == 5, (
            f"Only {mock_sdk_query['fully_consumed']}/{mock_sdk_query['total']} "
            "generators were fully consumed under parallel execution."
        )


@pytest.mark.no_mirror
def describe_generator_consumption_on_error():
    """Verify query_structured fully consumes SDK generator even on error paths.

    Exceptions inside the async for loop (ValidationError, StructuredOutputError)
    must be deferred until after the generator is consumed. Raising inside the
    loop abandons the generator, triggering anyio cancel scope RuntimeError
    under parallel execution.
    """

    @pytest.fixture(autouse=True)
    def mock_sdk_query():
        call_count = {"total": 0, "fully_consumed": 0}

        async def mock_query_gen(**kwargs) -> AsyncGenerator:  # noqa: ARG001
            call_count["total"] += 1
            for msg in [
                AssistantMessage(
                    content=[
                        ToolUseBlock(
                            id="tool-1",
                            name="StructuredOutput",
                            input={"wrong_field": "invalid"},
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
            ]:
                yield msg
            call_count["fully_consumed"] += 1

        with patch(
            "skillet._internal.sdk.query_structured.claude_agent_sdk.query",
            mock_query_gen,
        ):
            yield call_count

    @pytest.mark.asyncio
    async def it_consumes_generators_under_parallel_gather_despite_validation_errors(
        mock_sdk_query,
    ):
        """Parallel validation failures must still fully consume all generators."""
        from pydantic import ValidationError

        class StrictModel(BaseModel):
            required_field: int

        async def try_query(i: int) -> str:
            try:
                await query_structured(f"prompt {i}", StrictModel)
                return "ok"
            except ValidationError:
                return "validation_error"

        results = await asyncio.gather(*[try_query(i) for i in range(5)])

        assert all(r == "validation_error" for r in results)
        assert mock_sdk_query["total"] == 5
        assert mock_sdk_query["fully_consumed"] == 5, (
            f"Only {mock_sdk_query['fully_consumed']}/{mock_sdk_query['total']} "
            "generators were fully consumed despite ValidationError."
        )
