"""Fixtures for integration tests."""

from collections.abc import AsyncGenerator
from pathlib import Path
from unittest.mock import patch

import pytest


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

        def set_responses(*responses):
            """Configure multiple responses for sequential SDK calls.

            Each response can be:
            - A string (text response)
            - A dict (structured response)
            - An Exception (error)

            Usage:
                mock_claude_query.set_responses(
                    "Text response 1",                              # First call
                    {"pass": True, "reasoning": "Good"},           # Second call
                    RuntimeError("API error"),                     # Third call
                )
            """
            from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock

            async def mock_generator_factory(response):
                if isinstance(response, Exception):
                    raise response
                elif isinstance(response, dict):
                    # Structured response
                    yield ResultMessage(
                        subtype="result",
                        duration_ms=100,
                        duration_api_ms=100,
                        is_error=False,
                        num_turns=1,
                        session_id="mock-session",
                        result="",
                        structured_output=response,
                    )
                else:
                    # Text response
                    yield AssistantMessage(
                        content=[TextBlock(text=response)],
                        model="claude-sonnet-4-20250514",
                    )
                    yield ResultMessage(
                        subtype="result",
                        duration_ms=100,
                        duration_api_ms=100,
                        is_error=False,
                        num_turns=1,
                        session_id="mock-session",
                        result=response,
                        structured_output={"content": response},
                    )

            mock.side_effect = [mock_generator_factory(r) for r in responses]

        mock.set_response = set_response
        mock.set_structured_response = set_structured_response
        mock.set_error = set_error
        mock.set_responses = set_responses

        # Default response
        set_response("Default mocked response")

        yield mock
