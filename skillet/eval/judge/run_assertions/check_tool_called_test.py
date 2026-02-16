"""Tests for check_tool_called."""

from skillet.eval.judge.run_assertions.check_tool_called import check_tool_called


def describe_check_tool_called():
    def it_passes_when_tool_was_called():
        assert check_tool_called("Read", tool_names={"Read", "Write"}) is None

    def it_fails_when_tool_was_not_called():
        result = check_tool_called("Read", tool_names={"Write"})
        assert result is not None
        assert "tool_called" in result

    def it_fails_when_tool_names_empty():
        result = check_tool_called("Read", tool_names=set())
        assert result is not None
