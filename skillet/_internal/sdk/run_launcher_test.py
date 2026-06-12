"""Tests for the launcher-command agent runner."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from skillet._internal.sdk.run_launcher import run_launcher

_EXEC = "skillet._internal.sdk.run_launcher.asyncio.create_subprocess_exec"


def _fake_proc(stdout: bytes = b"", stderr: bytes = b"", returncode: int = 0):
    proc = MagicMock()
    proc.communicate = AsyncMock(return_value=(stdout, stderr))
    proc.returncode = returncode
    return proc


def _stream_json(*events: dict) -> bytes:
    return ("\n".join(json.dumps(e) for e in events) + "\n").encode()


def describe_run_launcher():
    @pytest.mark.asyncio
    async def it_returns_plain_text_output():
        with patch(_EXEC, new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _fake_proc(stdout=b"Hello world\n")

            result = await run_launcher(["hi"], launcher="myagent")

            assert result.text == "Hello world"
            assert result.tool_calls == []

    @pytest.mark.asyncio
    async def it_appends_the_prompt_and_passes_cwd_and_env():
        with patch(_EXEC, new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _fake_proc(stdout=b"ok")

            await run_launcher(["do it"], launcher="claude -p", cwd="/work", env={"HOME": "/h"})

            args, kwargs = mock_exec.call_args
            assert args == ("claude", "-p", "do it")
            assert kwargs["cwd"] == "/work"
            assert kwargs["env"] == {"HOME": "/h"}

    @pytest.mark.asyncio
    async def it_extracts_text_and_tool_calls_from_stream_json():
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
        with patch(_EXEC, new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _fake_proc(stdout=stdout)

            result = await run_launcher(["hi"], launcher="claude -p --output-format stream-json")

            assert result.text == "Ahoy matey"
            assert result.tool_calls == [{"name": "Read", "input": {"path": "/x"}}]

    @pytest.mark.asyncio
    async def it_falls_back_to_result_text_without_assistant_text():
        stdout = _stream_json({"type": "result", "result": "final answer"})
        with patch(_EXEC, new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _fake_proc(stdout=stdout)

            result = await run_launcher(["hi"], launcher="agent")

            assert result.text == "final answer"
            assert result.tool_calls == []

    @pytest.mark.asyncio
    async def it_runs_each_turn_and_accumulates_tool_calls():
        turn1 = _stream_json(
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "tool_use", "id": "1", "name": "Bash", "input": {}},
                        {"type": "text", "text": "one"},
                    ]
                },
            },
        )
        with patch(_EXEC, new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = [
                _fake_proc(stdout=turn1),
                _fake_proc(stdout=b"two"),
            ]

            result = await run_launcher(["a", "b"], launcher="agent")

            assert result.text == "two"
            assert result.tool_calls == [{"name": "Bash", "input": {}}]

    @pytest.mark.asyncio
    async def it_raises_on_nonzero_exit_with_no_output():
        with patch(_EXEC, new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _fake_proc(stderr=b"boom", returncode=1)

            with pytest.raises(RuntimeError, match="exited 1"):
                await run_launcher(["hi"], launcher="agent")

    @pytest.mark.asyncio
    async def it_raises_for_an_empty_launcher():
        with pytest.raises(ValueError, match="empty"):
            await run_launcher(["hi"], launcher="   ")
