"""Integration test fixtures."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def output_dir(tmp_path):
    """Create a temporary output directory for tests."""
    return tmp_path / "output"


@pytest.fixture(autouse=True)
def reset_client_and_cache(tmp_path):
    """Reset the global client and use a fresh cache directory."""
    import skill_collection.github as github_module

    github_module._client = None
    original_default = github_module.DEFAULT_CACHE_DIR
    github_module.DEFAULT_CACHE_DIR = tmp_path / ".cache"
    yield
    github_module._client = None
    github_module.DEFAULT_CACHE_DIR = original_default


@pytest.fixture
def mock_gh_cli():
    """Mock the gh CLI subprocess calls and time.sleep for speed."""
    with (
        patch("subprocess.run") as mock_run,
        patch("time.sleep"),  # Skip rate limit waits
    ):
        yield mock_run


@pytest.fixture(autouse=True)
def mock_claude_agent_sdk():
    """Mock the Claude Agent SDK at the boundary.

    Patches the SDK's query function inside agent.py so all downstream
    code (filter, classify) uses the mock automatically.
    """
    from claude_agent_sdk import ResultMessage

    call_count = [0]
    query_mock = MagicMock()

    async def mock_sdk_query(prompt, options):
        """Mock generator that yields a ResultMessage with JSON response."""
        query_mock(prompt=prompt, options=options)  # Track calls
        call_count[0] += 1
        # Default: first call returns True, subsequent calls return False
        is_skill = call_count[0] == 1
        result_json = json.dumps({"is_skill_file": is_skill, "reason": "test reason"})
        yield ResultMessage(
            subtype="result",
            duration_ms=0,
            duration_api_ms=0,
            is_error=False,
            num_turns=1,
            session_id="test",
            result=result_json,
        )

    mock = MagicMock()
    mock.query = query_mock
    mock._call_count = call_count

    with patch("skill_collection.agent.query", side_effect=lambda **kwargs: mock_sdk_query(**kwargs)):
        yield mock
