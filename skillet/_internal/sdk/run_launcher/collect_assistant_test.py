"""Tests for collecting text and tool calls from a stream-json assistant event."""

from .collect_assistant import collect_assistant


def describe_collect_assistant():
    def it_collects_text_blocks():
        text_parts: list[str] = []
        tool_calls: list[dict] = []
        event = {"message": {"content": [{"type": "text", "text": "hello"}]}}

        collect_assistant(event, text_parts, tool_calls)

        assert text_parts == ["hello"]
        assert tool_calls == []

    def it_collects_tool_use_blocks():
        text_parts: list[str] = []
        tool_calls: list[dict] = []
        event = {
            "message": {
                "content": [{"type": "tool_use", "id": "1", "name": "Bash", "input": {"cmd": "ls"}}]
            }
        }

        collect_assistant(event, text_parts, tool_calls)

        assert text_parts == []
        assert tool_calls == [{"name": "Bash", "input": {"cmd": "ls"}}]

    def it_collects_mixed_blocks_in_order():
        text_parts: list[str] = []
        tool_calls: list[dict] = []
        event = {
            "message": {
                "content": [
                    {"type": "text", "text": "a"},
                    {"type": "tool_use", "name": "Read", "input": {}},
                    {"type": "text", "text": "b"},
                ]
            }
        }

        collect_assistant(event, text_parts, tool_calls)

        assert text_parts == ["a", "b"]
        assert tool_calls == [{"name": "Read", "input": {}}]

    def it_defaults_missing_tool_fields():
        tool_calls: list[dict] = []
        event = {"message": {"content": [{"type": "tool_use"}]}}

        collect_assistant(event, [], tool_calls)

        assert tool_calls == [{"name": "", "input": {}}]

    def it_ignores_non_dict_blocks_and_unknown_types():
        text_parts: list[str] = []
        tool_calls: list[dict] = []
        event = {"message": {"content": ["nope", {"type": "thinking", "thinking": "x"}]}}

        collect_assistant(event, text_parts, tool_calls)

        assert text_parts == []
        assert tool_calls == []

    def it_handles_missing_or_non_list_content():
        text_parts: list[str] = []
        tool_calls: list[dict] = []

        collect_assistant({}, text_parts, tool_calls)
        collect_assistant({"message": {"content": "not a list"}}, text_parts, tool_calls)

        assert text_parts == []
        assert tool_calls == []
