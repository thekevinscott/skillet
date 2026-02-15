"""Tests for judge/format_tool_calls module."""

from skillet.eval.judge.format_tool_calls import format_tool_calls


def describe_format_tool_calls():
    def it_returns_no_tools_message_for_empty_list():
        result = format_tool_calls([])
        assert result == "(no tools used)"

    def it_formats_single_tool_call():
        tool_calls = [{"name": "read_file", "input": {"path": "/test.txt"}}]
        result = format_tool_calls(tool_calls)
        assert "read_file" in result
        assert "/test.txt" in result

    def it_formats_multiple_tool_calls():
        tool_calls = [
            {"name": "read_file", "input": {"path": "/a.txt"}},
            {"name": "write_file", "input": {"path": "/b.txt", "content": "hello"}},
        ]
        result = format_tool_calls(tool_calls)
        assert "read_file" in result
        assert "write_file" in result
        assert "/a.txt" in result
        assert "/b.txt" in result

    def it_handles_empty_input():
        tool_calls = [{"name": "some_tool", "input": {}}]
        result = format_tool_calls(tool_calls)
        assert "some_tool" in result

    def it_handles_missing_input_key():
        tool_calls = [{"name": "some_tool"}]
        result = format_tool_calls(tool_calls)
        assert "some_tool" in result
