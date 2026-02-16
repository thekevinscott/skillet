"""Tests for get_symbol_and_counts."""

import pytest

from .get_symbol_and_counts import get_symbol_and_counts
from .status_symbols import CACHED, FAIL, PASS, PENDING, RUNNING


@pytest.mark.parametrize(
    "state,result,expected_symbol,expected_passed,expected_done",
    [
        ("pending", None, PENDING, False, False),
        ("running", None, RUNNING, False, False),
        ("cached", {"pass": True}, CACHED, True, True),
        ("cached", {"pass": False}, CACHED, False, True),
        ("done", {"pass": True}, PASS, True, True),
        ("done", {"pass": False}, FAIL, False, True),
        ("done", None, FAIL, None, True),  # None result -> passed is None (falsy)
    ],
    ids=[
        "pending",
        "running",
        "cached_pass",
        "cached_fail",
        "done_pass",
        "done_fail",
        "done_none_result",
    ],
)
def test_get_symbol_and_counts(state, result, expected_symbol, expected_passed, expected_done):
    """Test get_symbol_and_counts returns correct values for each state."""
    symbol, passed, done = get_symbol_and_counts({"state": state, "result": result})
    assert symbol == expected_symbol
    # For None result, passed is None (falsy), so check truthiness
    assert bool(passed) == bool(expected_passed)
    assert done == expected_done
