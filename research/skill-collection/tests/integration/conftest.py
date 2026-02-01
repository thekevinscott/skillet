"""Integration test fixtures."""

import importlib
import json
import sys
from unittest.mock import MagicMock, patch

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
    """Mock the claude_agent_sdk module for all integration tests.

    This fixture:
    - Mocks the entire claude_agent_sdk module as an external dependency
    - Sets up reasonable defaults for ResultMessage and query
    - Can be configured per-test by accessing the fixture parameter
    """
    # Create mock module
    mock_sdk = MagicMock()

    # Create a ResultMessage class that can be used for isinstance checks
    class MockResultMessage:
        def __init__(self, result=None, is_error=False):
            self.result = result
            self.is_error = is_error
            self.structured_output = None  # Not used in current implementation

    mock_sdk.ResultMessage = MockResultMessage
    mock_sdk.ClaudeAgentOptions = MagicMock()

    # Default query behavior - can be overridden per test
    call_count = [0]

    async def default_query_generator():
        call_count[0] += 1
        # Default: first call returns True, subsequent calls return False
        is_skill = call_count[0] == 1
        result = {"is_skill_file": is_skill, "reason": "test reason"}
        yield MockResultMessage(result=json.dumps(result))

    mock_sdk.query = MagicMock(side_effect=lambda *args, **kwargs: default_query_generator())
    mock_sdk._call_count = call_count  # Expose for test assertions

    # Install mock module before any imports
    sys.modules["claude_agent_sdk"] = mock_sdk

    # Force reload of only the filter module so it picks up the mock
    # Don't reload skill_collection itself as it causes dataclass identity issues
    if "skill_collection.filter" in sys.modules:
        importlib.reload(sys.modules["skill_collection.filter"])

    yield mock_sdk

    # Cleanup
    del sys.modules["claude_agent_sdk"]
