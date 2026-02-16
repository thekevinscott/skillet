"""Fixtures for integration tests."""

from collections.abc import AsyncGenerator
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import pytest

_FIXTURES_DIR = Path(__file__).parent.parent / "__fixtures__"

SAMPLE_SKILL = (_FIXTURES_DIR / "sample_skill.txt").read_text()
COMPLEX_SKILL = (_FIXTURES_DIR / "complex_skill.txt").read_text()

SAMPLE_GENERATED_EVALS = {
    "candidates": [
        {
            "prompt": "I tried to fetch https://api.example.com/data but WebFetch failed",
            "expected": "Suggests curl with appropriate flags",
            "name": "positive-goal1-browser-fail",
            "category": "positive",
            "domain": "triggering",
            "source": "goal:1",
            "confidence": 0.85,
            "rationale": "Tests the primary goal of suggesting curl on browser failure",
        },
        {
            "prompt": "Please fetch this JavaScript-heavy SPA page",
            "expected": "Warns that curl won't execute JavaScript",
            "name": "positive-goal3-js-warning",
            "category": "positive",
            "domain": "functional",
            "source": "goal:3",
            "confidence": 0.75,
            "rationale": "Tests handling of JS-heavy pages per prohibition",
        },
        {
            "prompt": "The browser timed out, try again please",
            "expected": "Should NOT retry browser operation multiple times",
            "name": "negative-prohibition1-no-retry",
            "category": "negative",
            "domain": "triggering",
            "source": "prohibition:1",
            "confidence": 0.9,
            "rationale": "Tests the prohibition against multiple retries",
        },
    ]
}

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
    import yaml

    defaults = {
        "timestamp": "2025-01-01T00:00:00Z",
        "prompt": "Test prompt",
        "expected": "Test expected behavior",
        "name": "test-skill",
    }
    defaults.update(overrides)

    path.write_text(yaml.dump(defaults, default_flow_style=False, sort_keys=False))


@pytest.fixture(autouse=True)
def mock_cachetta():
    """Mock cachetta to avoid depending on its pickle serialization."""
    cache_store: dict[str, object] = {}

    def mock_write(cache, data, *args, **kwargs):
        path = cache._get_path(*args, **kwargs)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()  # Stub file so glob finds it
        cache_store[str(path)] = data

    @contextmanager
    def mock_read(cache=None, *args, **kwargs):
        if cache is None:
            yield None
        else:
            path = cache._get_path(*args, **kwargs)
            yield cache_store.get(str(path))

    with (
        patch("cachetta.write_cache", side_effect=mock_write),
        patch("cachetta.read_cache", mock_read),
    ):
        yield


@pytest.fixture
def skillet_env(tmp_path: Path, monkeypatch):
    """Set up isolated SKILLET_DIR for testing."""
    skillet_dir = tmp_path / ".skillet"
    skillet_dir.mkdir()
    (skillet_dir / "evals").mkdir()

    # Patch SKILLET_DIR and CACHE_DIR in config (all modules reference config.* at runtime)
    import skillet.config
    import skillet.evals.load

    monkeypatch.setattr(skillet.config, "SKILLET_DIR", skillet_dir)
    monkeypatch.setattr(skillet.config, "CACHE_DIR", skillet_dir / "cache")
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

        def set_text_only_response(response_text: str):
            """Configure the mock to return only text with no StructuredOutput.

            Reproduces the failure mode where the LLM exhausts its output
            budget on text content and never produces a tool call.
            """
            from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock

            async def mock_generator() -> AsyncGenerator:
                yield AssistantMessage(
                    content=[TextBlock(text=response_text)],
                    model="claude-sonnet-4-20250514",
                )
                yield ResultMessage(
                    subtype="result",
                    duration_ms=373000,
                    duration_api_ms=373000,
                    is_error=False,
                    num_turns=1,
                    session_id="mock-session",
                    result=response_text,
                    structured_output=None,
                )

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
        mock.set_text_only_response = set_text_only_response
        mock.set_structured_response = set_structured_response
        mock.set_error = set_error
        mock.set_responses = set_responses

        # Default response
        set_response("Default mocked response")

        yield mock
