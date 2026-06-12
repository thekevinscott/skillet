"""Tests for parsing launcher stdout (stream-json or plain text)."""

import json

from skillet._internal.sdk.run_launcher.parse_launcher_output import parse_launcher_output


def _stream_json(*events: dict) -> str:
    return "\n".join(json.dumps(e) for e in events) + "\n"


def describe_parse_launcher_output():
    def it_returns_plain_text_for_non_json():
        text, tool_calls = parse_launcher_output("just some text\n")
        assert text == "just some text"
        assert tool_calls == []

    def it_extracts_text_and_tool_calls_from_stream_json():
        stdout = _stream_json(
            {"type": "system", "subtype": "init", "session_id": "s1"},
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "text", "text": "Ahoy "},
                        {"type": "tool_use", "id": "1", "name": "Read", "input": {"path": "/x"}},
                    ]
                },
            },
            {"type": "assistant", "message": {"content": [{"type": "text", "text": "matey"}]}},
            {"type": "result", "subtype": "success", "result": "Ahoy matey"},
        )
        text, tool_calls = parse_launcher_output(stdout)
        assert text == "Ahoy matey"
        assert tool_calls == [{"name": "Read", "input": {"path": "/x"}}]

    def it_falls_back_to_result_text_without_assistant_text():
        stdout = _stream_json({"type": "result", "result": "final answer"})
        text, tool_calls = parse_launcher_output(stdout)
        assert text == "final answer"
        assert tool_calls == []

    def it_ignores_unparseable_lines_in_otherwise_text_output():
        text, tool_calls = parse_launcher_output("line one\nnot json {\nline two")
        assert text == "line one\nnot json {\nline two"
        assert tool_calls == []
