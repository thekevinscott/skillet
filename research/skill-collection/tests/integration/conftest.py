"""Integration test fixtures."""

import importlib
import json
import sys
from unittest.mock import MagicMock

import pytest


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
