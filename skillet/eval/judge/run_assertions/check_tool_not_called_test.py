"""Tests for check_tool_not_called."""

from skillet.eval.judge.run_assertions.check_tool_not_called import check_tool_not_called


def describe_check_tool_not_called():
    def it_passes_when_tool_was_not_called():
        assert check_tool_not_called("Read", tool_names={"Write"}) is None

    def it_fails_when_tool_was_called():
        result = check_tool_not_called("Read", tool_names={"Read", "Write"})
        assert result is not None
        assert "tool_not_called" in result

    def it_passes_when_tool_names_empty():
        assert check_tool_not_called("Read", tool_names=set()) is None
