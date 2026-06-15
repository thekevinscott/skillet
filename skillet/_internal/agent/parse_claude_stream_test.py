"""Tests for parse_claude_stream."""

import json

from skillet._internal.agent.parse_claude_stream import parse_claude_stream


def _line(obj: dict) -> str:
    return json.dumps(obj)


def describe_parse_claude_stream():
    """Tests for parsing Claude CLI stream-json output."""

    def it_extracts_text_from_assistant_blocks():
        stdout = "\n".join(
            [
                _line({"type": "system", "subtype": "init", "session_id": "s1"}),
                _line(
                    {
                        "type": "assistant",
                        "message": {"content": [{"type": "text", "text": "hello world"}]},
                    }
                ),
                _line({"type": "result", "subtype": "success", "result": "hello world"}),
            ]
        )

        text, tool_calls, session_id = parse_claude_stream(stdout)

        assert text == "hello world"
        assert tool_calls == []
        assert session_id == "s1"

    def it_collects_tool_calls():
        stdout = "\n".join(
            [
                _line({"type": "system", "subtype": "init", "session_id": "s1"}),
                _line(
                    {
                        "type": "assistant",
                        "message": {
                            "content": [
                                {"type": "tool_use", "name": "Skill", "input": {"skill": "x"}},
                                {"type": "text", "text": "done"},
                            ]
                        },
                    }
                ),
            ]
        )

        text, tool_calls, _ = parse_claude_stream(stdout)

        assert text == "done"
        assert tool_calls == [{"name": "Skill", "input": {"skill": "x"}}]

    def it_falls_back_to_result_text_when_no_assistant_text():
        stdout = "\n".join(
            [
                _line({"type": "system", "subtype": "init", "session_id": "s1"}),
                _line({"type": "result", "subtype": "success", "result": "final answer"}),
            ]
        )

        text, tool_calls, _ = parse_claude_stream(stdout)

        assert text == "final answer"
        assert tool_calls == []

    def it_returns_none_session_id_when_absent():
        stdout = _line(
            {"type": "assistant", "message": {"content": [{"type": "text", "text": "hi"}]}}
        )

        _, _, session_id = parse_claude_stream(stdout)

        assert session_id is None

    def it_skips_malformed_lines():
        stdout = "\n".join(
            [
                "not json",
                "",
                _line(
                    {
                        "type": "assistant",
                        "message": {"content": [{"type": "text", "text": "ok"}]},
                    }
                ),
            ]
        )

        text, _, _ = parse_claude_stream(stdout)

        assert text == "ok"

    def it_concatenates_multiple_text_blocks():
        stdout = "\n".join(
            [
                _line(
                    {
                        "type": "assistant",
                        "message": {"content": [{"type": "text", "text": "foo "}]},
                    }
                ),
                _line(
                    {
                        "type": "assistant",
                        "message": {"content": [{"type": "text", "text": "bar"}]},
                    }
                ),
            ]
        )

        text, _, _ = parse_claude_stream(stdout)

        assert text == "foo bar"
