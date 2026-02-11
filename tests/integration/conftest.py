"""Fixtures for integration tests."""

from collections.abc import AsyncGenerator
from pathlib import Path
from unittest.mock import patch

import pytest

_TOOL_USE_COUNTER = 0


def _next_tool_use_id() -> str:
    global _TOOL_USE_COUNTER
    _TOOL_USE_COUNTER += 1
    return f"mock-tool-use-{_TOOL_USE_COUNTER}"


def _structured_output_messages(data: dict) -> list:
    """Build the real SDK message sequence for structured output.

    The real SDK delivers structured output as:
    1. AssistantMessage with ToolUseBlock(name='StructuredOutput', input=data)
    2. UserMessage with ToolResultBlock
    3. ResultMessage with structured_output=None
    """
    from claude_agent_sdk import (
        AssistantMessage,
        ResultMessage,
        ToolResultBlock,
        ToolUseBlock,
        UserMessage,
    )

    tool_use_id = _next_tool_use_id()
    return [
        AssistantMessage(
            content=[ToolUseBlock(id=tool_use_id, name="StructuredOutput", input=data)],
            model="claude-sonnet-4-20250514",
        ),
        UserMessage(
            content=[
                ToolResultBlock(
                    tool_use_id=tool_use_id,
                    content="Structured output provided successfully",
                )
            ],
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


def create_eval_file(path: Path, **overrides) -> None:
    """Create a valid eval YAML file with optional field overrides."""
    defaults = {
        "timestamp": "2025-01-01T00:00:00Z",
        "prompt": "Test prompt",
        "expected": "Test expected behavior",
        "name": "test-skill",
    }
    defaults.update(overrides)

    lines = [f"{k}: {v!r}" if isinstance(v, str) else f"{k}: {v}" for k, v in defaults.items()]
    path.write_text("\n".join(lines) + "\n")


@pytest.fixture
def skillet_env(tmp_path: Path, monkeypatch):
    """Set up isolated SKILLET_DIR for testing."""
    skillet_dir = tmp_path / ".skillet"
    skillet_dir.mkdir()
    (skillet_dir / "evals").mkdir()

    # Patch SKILLET_DIR in all modules that import it
    import skillet.config
    import skillet.evals.load

    monkeypatch.setattr(skillet.config, "SKILLET_DIR", skillet_dir)
    monkeypatch.setattr(skillet.evals.load, "SKILLET_DIR", skillet_dir)

    return tmp_path


@pytest.fixture
def mock_claude_query():
    """Mock claude_agent_sdk.query() with configurable responses.

    Produces the same message sequence as the real SDK:
    - Text responses: AssistantMessage(TextBlock) + StructuredOutput tool-use sequence
    - Structured output: ToolUseBlock + ToolResultBlock + ResultMessage sequence
    """
    with patch("claude_agent_sdk.query") as mock:

        def set_response(response_text: str):
            """Configure the mock to return a specific text response.

            Yields AssistantMessage with text for query_assistant_text,
            followed by StructuredOutput tool-use sequence for query_structured.
            """
            from claude_agent_sdk import AssistantMessage, TextBlock

            async def mock_generator() -> AsyncGenerator:
                yield AssistantMessage(
                    content=[TextBlock(text=response_text)],
                    model="claude-sonnet-4-20250514",
                )
                for msg in _structured_output_messages({"content": response_text}):
                    yield msg

            mock.return_value = mock_generator()

        def set_structured_response(data: dict):
            """Configure the mock to return a structured output response."""

            async def mock_generator() -> AsyncGenerator:
                for msg in _structured_output_messages(data):
                    yield msg

            mock.return_value = mock_generator()

        def set_error(exception: Exception):
            """Configure the mock to raise an exception."""

            async def error_generator() -> AsyncGenerator:
                raise exception
                yield  # type: ignore[misc]  # Make it a generator

            mock.return_value = error_generator()

        def set_responses(*responses):
            """Configure multiple responses for sequential SDK calls.

            Each response can be:
            - A string (text response)
            - A dict (structured response)
            - An Exception (error)
            """
            from claude_agent_sdk import AssistantMessage, TextBlock

            async def mock_generator_factory(response):
                if isinstance(response, Exception):
                    raise response
                elif isinstance(response, dict):
                    for msg in _structured_output_messages(response):
                        yield msg
                else:
                    yield AssistantMessage(
                        content=[TextBlock(text=response)],
                        model="claude-sonnet-4-20250514",
                    )
                    for msg in _structured_output_messages({"content": response}):
                        yield msg

            mock.side_effect = [mock_generator_factory(r) for r in responses]

        mock.set_response = set_response
        mock.set_structured_response = set_structured_response
        mock.set_error = set_error
        mock.set_responses = set_responses

        # Default response
        set_response("Default mocked response")

        yield mock
