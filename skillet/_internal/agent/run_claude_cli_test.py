"""Tests for run_claude_cli."""

import json
from typing import cast
from unittest.mock import AsyncMock, patch

import pytest


def _stream(text: str = "", *, session_id: str | None = None, tool: str | None = None) -> bytes:
    lines = []
    if session_id:
        lines.append(json.dumps({"type": "system", "subtype": "init", "session_id": session_id}))
    content: list[dict] = []
    if tool:
        content.append({"type": "tool_use", "name": tool, "input": {}})
    if text:
        content.append({"type": "text", "text": text})
    if content:
        lines.append(json.dumps({"type": "assistant", "message": {"content": content}}))
    return "\n".join(lines).encode()


class _FakeProc:
    def __init__(self, stdout: bytes, *, returncode: int = 0, stderr: bytes = b""):
        self._stdout = stdout
        self._stderr = stderr
        self.returncode = returncode

    async def communicate(self) -> tuple[bytes, bytes]:
        return self._stdout, self._stderr


def describe_run_claude_cli():
    """Tests for driving the claude CLI as the agent under test."""

    @pytest.mark.asyncio
    async def it_raises_when_cli_missing():
        from skillet._internal.agent.run_claude_cli import run_claude_cli

        with (
            patch("skillet._internal.agent.run_claude_cli.which", return_value=None),
            pytest.raises(RuntimeError, match=r"claude.*not found"),
        ):
            await run_claude_cli(["hi"])

    @pytest.mark.asyncio
    async def it_returns_text_and_tool_calls():
        from skillet._internal.agent.run_claude_cli import run_claude_cli

        proc = _FakeProc(_stream("done", session_id="s1", tool="Skill"))
        exec_mock = AsyncMock(return_value=cast("object", proc))

        with (
            patch("skillet._internal.agent.run_claude_cli.which", return_value="/usr/bin/claude"),
            patch("skillet._internal.agent.run_claude_cli.create_subprocess_exec", exec_mock),
        ):
            result = await run_claude_cli(["hi"])

        assert result.text == "done"
        assert result.tool_calls == [{"name": "Skill", "input": {}}]

    @pytest.mark.asyncio
    async def it_includes_base_flags_and_allowed_tools_in_command():
        from skillet._internal.agent.run_claude_cli import run_claude_cli

        proc = _FakeProc(_stream("ok", session_id="s1"))
        exec_mock = AsyncMock(return_value=cast("object", proc))

        with (
            patch("skillet._internal.agent.run_claude_cli.which", return_value="/usr/bin/claude"),
            patch("skillet._internal.agent.run_claude_cli.create_subprocess_exec", exec_mock),
        ):
            await run_claude_cli(["hi"], allowed_tools=["Skill", "Bash"])

        cmd = exec_mock.call_args.args
        assert cmd[0] == "claude"
        assert "--output-format" in cmd
        assert "stream-json" in cmd
        assert "--permission-mode" in cmd
        assert "bypassPermissions" in cmd
        assert "--allowedTools" in cmd
        assert "Skill" in cmd
        assert "Bash" in cmd
        assert cmd[-1] == "hi"

    @pytest.mark.asyncio
    async def it_resumes_session_on_subsequent_turns():
        from skillet._internal.agent.run_claude_cli import run_claude_cli

        procs = [
            _FakeProc(_stream("turn1", session_id="sess-abc")),
            _FakeProc(_stream("turn2")),
        ]
        exec_mock = AsyncMock(side_effect=[cast("object", p) for p in procs])

        with (
            patch("skillet._internal.agent.run_claude_cli.which", return_value="/usr/bin/claude"),
            patch("skillet._internal.agent.run_claude_cli.create_subprocess_exec", exec_mock),
        ):
            result = await run_claude_cli(["one", "two"])

        first_cmd = exec_mock.call_args_list[0].args
        second_cmd = exec_mock.call_args_list[1].args
        assert "--resume" not in first_cmd
        assert "--resume" in second_cmd
        assert "sess-abc" in second_cmd
        assert result.text == "turn2"

    @pytest.mark.asyncio
    async def it_passes_cwd_and_env_to_subprocess():
        from skillet._internal.agent.run_claude_cli import run_claude_cli

        proc = _FakeProc(_stream("ok", session_id="s1"))
        exec_mock = AsyncMock(return_value=cast("object", proc))

        with (
            patch("skillet._internal.agent.run_claude_cli.which", return_value="/usr/bin/claude"),
            patch("skillet._internal.agent.run_claude_cli.create_subprocess_exec", exec_mock),
        ):
            await run_claude_cli(["hi"], cwd="/sandbox", env={"HOME": "/tmp/home"})

        assert exec_mock.call_args.kwargs["cwd"] == "/sandbox"
        assert exec_mock.call_args.kwargs["env"] == {"HOME": "/tmp/home"}

    @pytest.mark.asyncio
    async def it_raises_on_nonzero_exit_without_text():
        from skillet._internal.agent.run_claude_cli import run_claude_cli

        proc = _FakeProc(b"", returncode=1, stderr=b"boom")
        exec_mock = AsyncMock(return_value=cast("object", proc))

        with (
            patch("skillet._internal.agent.run_claude_cli.which", return_value="/usr/bin/claude"),
            patch("skillet._internal.agent.run_claude_cli.create_subprocess_exec", exec_mock),
            pytest.raises(RuntimeError, match=r"exited with code 1.*boom"),
        ):
            await run_claude_cli(["hi"])
