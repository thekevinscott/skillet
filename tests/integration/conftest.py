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
    """
    with patch("skillet._internal.sdk.query") as mock:

        def set_response(response_text: str):
            """Configure the mock to return a specific response."""
            from claude_agent_sdk import AssistantMessage, TextBlock

            async def mock_generator() -> AsyncGenerator:
                msg = AssistantMessage(
                    content=[TextBlock(text=response_text)],
                    model="claude-sonnet-4-20250514",
                )
                yield msg

            mock.return_value = mock_generator()

        def set_error(exception: Exception):
            """Configure the mock to raise an exception."""

            async def error_generator() -> AsyncGenerator:
                raise exception
                yield  # type: ignore[misc]  # Make it a generator

            mock.return_value = error_generator()

        mock.set_response = set_response
        mock.set_error = set_error

        # Default response
        set_response("Default mocked response")

        yield mock
