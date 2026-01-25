"""Fixtures for integration tests."""

from collections.abc import AsyncGenerator
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_claude_query():
    """Mock claude_agent_sdk.query() with configurable responses.

    Usage:
        def test_something(mock_claude_query):
            mock_claude_query.set_response("Generated content here")
            # ... run code that calls the SDK

        # For structured output with custom data:
        def test_structured(mock_claude_query):
            mock_claude_query.set_structured_response({"pass": True, "reasoning": "OK"})
    """
    with patch("claude_agent_sdk.query") as mock:

        def set_response(response_text: str):
            """Configure the mock to return a specific text response.

            Yields both AssistantMessage (for query_assistant_text) and
            ResultMessage with structured_output (for query_structured with SkillContent).
            """
            from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock

            async def mock_generator() -> AsyncGenerator:
                # Yield AssistantMessage for query_assistant_text
                yield AssistantMessage(
                    content=[TextBlock(text=response_text)],
                    model="claude-sonnet-4-20250514",
                )
                # Yield ResultMessage with structured_output for query_structured
                # Uses {"content": text} format compatible with SkillContent model
                yield ResultMessage(
                    subtype="result",
                    duration_ms=100,
                    duration_api_ms=100,
                    is_error=False,
                    num_turns=1,
                    session_id="mock-session",
                    result=response_text,
                    structured_output={"content": response_text},
                )

            mock.return_value = mock_generator()

        def set_structured_response(data: dict):
            """Configure the mock to return a structured output response.

            Use this for query_structured with custom models (e.g., Judgment).
            """
            from claude_agent_sdk import ResultMessage

            async def mock_generator() -> AsyncGenerator:
                yield ResultMessage(
                    subtype="result",
                    duration_ms=100,
                    duration_api_ms=100,
                    is_error=False,
                    num_turns=1,
                    session_id="mock-session",
                    result="",
                    structured_output=data,
                )

            mock.return_value = mock_generator()

        def set_error(exception: Exception):
            """Configure the mock to raise an exception."""

            async def error_generator() -> AsyncGenerator:
                raise exception
                yield  # type: ignore[misc]  # Make it a generator

            mock.return_value = error_generator()

        mock.set_response = set_response
        mock.set_structured_response = set_structured_response
        mock.set_error = set_error

        # Default response
        set_response("Default mocked response")

        yield mock
