"""Tests for parse_codex_stream."""

import json

from skillet._internal.agent.parse_codex_stream import parse_codex_stream


def _line(obj: dict) -> str:
    return json.dumps(obj)


def describe_parse_codex_stream():
    """Tests for parsing one turn of ``codex exec --json`` JSONL output."""

    def it_returns_the_last_agent_message_as_text():
        stdout = "\n".join(
            [
                _line({"type": "thread.started", "thread_id": "t-1"}),
                _line({"type": "turn.started"}),
                _line(
                    {
                        "type": "item.completed",
                        "item": {"id": "m1", "type": "agent_message", "text": "first"},
                    }
                ),
                _line(
                    {
                        "type": "item.completed",
                        "item": {"id": "m2", "type": "agent_message", "text": "final answer"},
                    }
                ),
                _line({"type": "turn.completed", "usage": {}}),
            ]
        )

        text, tool_calls, thread_id, error = parse_codex_stream(stdout)

        assert text == "final answer"
        assert tool_calls == []
        assert thread_id == "t-1"
        assert error is None

    def it_collects_command_execution_tool_calls():
        stdout = "\n".join(
            [
                _line({"type": "thread.started", "thread_id": "t-2"}),
                _line(
                    {
                        "type": "item.completed",
                        "item": {
                            "id": "c1",
                            "type": "command_execution",
                            "status": "completed",
                            "command": "ls -la",
                            "exit_code": 0,
                            "aggregated_output": "file.txt",
                        },
                    }
                ),
                _line(
                    {
                        "type": "item.completed",
                        "item": {"id": "m1", "type": "agent_message", "text": "done"},
                    }
                ),
            ]
        )

        text, tool_calls, _thread_id, _error = parse_codex_stream(stdout)

        assert text == "done"
        assert tool_calls == [
            {
                "name": "command_execution",
                "input": {
                    "command": "ls -la",
                    "exit_code": 0,
                    "aggregated_output": "file.txt",
                },
            }
        ]

    def it_collects_mcp_web_and_file_change_tool_calls():
        stdout = "\n".join(
            [
                _line(
                    {
                        "type": "item.completed",
                        "item": {
                            "id": "x1",
                            "type": "mcp_tool_call",
                            "status": "completed",
                            "server": "fs",
                            "tool": "read",
                            "arguments": {"path": "a"},
                        },
                    }
                ),
                _line(
                    {
                        "type": "item.completed",
                        "item": {
                            "id": "x2",
                            "type": "web_search",
                            "status": "completed",
                            "query": "python asyncio",
                        },
                    }
                ),
                _line(
                    {
                        "type": "item.completed",
                        "item": {
                            "id": "x3",
                            "type": "file_change",
                            "status": "completed",
                            "changes": [{"path": "a.py", "kind": "update"}],
                        },
                    }
                ),
            ]
        )

        _text, tool_calls, _thread_id, _error = parse_codex_stream(stdout)

        names = [c["name"] for c in tool_calls]
        assert names == ["mcp_tool_call", "web_search", "file_change"]
        assert tool_calls[0]["input"] == {
            "server": "fs",
            "tool": "read",
            "arguments": {"path": "a"},
        }
        assert tool_calls[1]["input"] == {"query": "python asyncio"}
        assert tool_calls[2]["input"] == {"changes": [{"path": "a.py", "kind": "update"}]}

    def it_ignores_reasoning_and_other_item_types():
        stdout = "\n".join(
            [
                _line(
                    {
                        "type": "item.completed",
                        "item": {"id": "r1", "type": "reasoning", "text": "thinking..."},
                    }
                ),
                _line(
                    {
                        "type": "item.completed",
                        "item": {
                            "id": "t1",
                            "type": "todo_list",
                            "items": [{"text": "do", "completed": False}],
                        },
                    }
                ),
                _line(
                    {
                        "type": "item.completed",
                        "item": {"id": "m1", "type": "agent_message", "text": "answer"},
                    }
                ),
            ]
        )

        text, tool_calls, _thread_id, _error = parse_codex_stream(stdout)

        assert text == "answer"
        assert tool_calls == []

    def it_captures_turn_failed_as_error():
        stdout = "\n".join(
            [
                _line({"type": "thread.started", "thread_id": "t-3"}),
                _line(
                    {
                        "type": "turn.failed",
                        "error": {"message": "model 'gpt-5.3-codex' is not supported"},
                    }
                ),
            ]
        )

        text, _tool_calls, _thread_id, error = parse_codex_stream(stdout)

        assert text == ""
        assert error == "model 'gpt-5.3-codex' is not supported"

    def it_captures_top_level_error():
        stdout = _line({"type": "error", "message": "stream broke"})

        _text, _tool_calls, _thread_id, error = parse_codex_stream(stdout)

        assert error == "stream broke"

    def it_skips_blank_and_malformed_lines():
        stdout = "\n".join(
            [
                "",
                "not json at all",
                _line({"type": "item.completed", "item": {"type": "agent_message", "text": "ok"}}),
                "   ",
            ]
        )

        text, tool_calls, _thread_id, error = parse_codex_stream(stdout)

        assert text == "ok"
        assert tool_calls == []
        assert error is None

    def it_returns_empty_when_no_agent_message():
        stdout = _line({"type": "thread.started", "thread_id": "t-4"})

        text, tool_calls, thread_id, error = parse_codex_stream(stdout)

        assert text == ""
        assert tool_calls == []
        assert thread_id == "t-4"
        assert error is None
