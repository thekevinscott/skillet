"""Tests for sdk module."""

from skillet._internal.sdk import QueryResult


def describe_QueryResult():
    """Tests for QueryResult dataclass."""

    def it_creates_with_text_only():
        result = QueryResult(text="hello world")
        assert result.text == "hello world"
        assert result.tool_calls == []

    def it_creates_with_text_and_tool_calls():
        tool_calls = [{"name": "read_file", "input": {"path": "/test"}}]
        result = QueryResult(text="response", tool_calls=tool_calls)
        assert result.text == "response"
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0]["name"] == "read_file"

    def it_has_empty_tool_calls_by_default():
        result = QueryResult(text="test")
        assert result.tool_calls == []
        # Verify it's a new list each time (not shared)
        result.tool_calls.append({"name": "test"})
        result2 = QueryResult(text="test2")
        assert result2.tool_calls == []
