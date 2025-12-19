"""Tests for eval/judge module."""

from skillet.eval.judge import format_prompt_for_judge, format_tool_calls_for_judge


def describe_format_prompt_for_judge():
    """Tests for format_prompt_for_judge function."""

    def it_returns_string_prompt_unchanged():
        result = format_prompt_for_judge("simple prompt")
        assert result == "simple prompt"

    def it_formats_multi_turn_prompts():
        prompts = ["first message", "second message", "third message"]
        result = format_prompt_for_judge(prompts)
        assert "Turn 1: first message" in result
        assert "Turn 2: second message" in result
        assert "Turn 3: third message" in result

    def it_handles_single_item_list():
        result = format_prompt_for_judge(["only one"])
        assert result == "Turn 1: only one"


def describe_format_tool_calls_for_judge():
    """Tests for format_tool_calls_for_judge function."""

    def it_returns_no_tools_message_for_empty_list():
        result = format_tool_calls_for_judge([])
        assert result == "(no tools used)"

    def it_formats_single_tool_call():
        tool_calls = [{"name": "read_file", "input": {"path": "/test.txt"}}]
        result = format_tool_calls_for_judge(tool_calls)
        assert "read_file" in result
        assert "/test.txt" in result

    def it_formats_multiple_tool_calls():
        tool_calls = [
            {"name": "read_file", "input": {"path": "/a.txt"}},
            {"name": "write_file", "input": {"path": "/b.txt", "content": "hello"}},
        ]
        result = format_tool_calls_for_judge(tool_calls)
        assert "read_file" in result
        assert "write_file" in result
        assert "/a.txt" in result
        assert "/b.txt" in result

    def it_handles_empty_input():
        tool_calls = [{"name": "some_tool", "input": {}}]
        result = format_tool_calls_for_judge(tool_calls)
        assert "some_tool" in result

    def it_handles_missing_input_key():
        tool_calls = [{"name": "some_tool"}]
        result = format_tool_calls_for_judge(tool_calls)
        assert "some_tool" in result
