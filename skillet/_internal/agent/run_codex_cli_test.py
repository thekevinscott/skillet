"""Tests for run_codex_cli."""

import json
from typing import cast
from unittest.mock import AsyncMock, patch

import pytest


def _stream(
    text: str = "",
    *,
    thread_id: str | None = None,
    tool: str | None = None,
    error: str | None = None,
) -> bytes:
    lines = []
    if thread_id:
        lines.append(json.dumps({"type": "thread.started", "thread_id": thread_id}))
    if tool:
        lines.append(
            json.dumps(
                {
                    "type": "item.completed",
                    "item": {"id": "c1", "type": tool, "status": "completed", "command": "ls"},
                }
            )
        )
    if text:
        lines.append(
            json.dumps(
                {
                    "type": "item.completed",
                    "item": {"id": "m1", "type": "agent_message", "text": text},
                }
            )
        )
    if error:
        lines.append(json.dumps({"type": "turn.failed", "error": {"message": error}}))
    return "\n".join(lines).encode()


class _FakeProc:
    def __init__(self, stdout: bytes, *, returncode: int = 0, stderr: bytes = b""):
        self._stdout = stdout
        self._stderr = stderr
        self.returncode = returncode

    async def communicate(self) -> tuple[bytes, bytes]:
        return self._stdout, self._stderr


def describe_run_codex_cli():
    """Tests for driving the codex CLI as the agent under test."""

    @pytest.mark.asyncio
    async def it_raises_when_cli_missing():
        from skillet._internal.agent.run_codex_cli import run_codex_cli

        with (
            patch("skillet._internal.agent.run_codex_cli.which", return_value=None),
            pytest.raises(RuntimeError, match=r"codex.*not found"),
        ):
            await run_codex_cli(["hi"])

    @pytest.mark.asyncio
    async def it_returns_text_and_tool_calls():
        from skillet._internal.agent.run_codex_cli import run_codex_cli

        proc = _FakeProc(_stream("done", thread_id="t1", tool="command_execution"))
        exec_mock = AsyncMock(return_value=cast("object", proc))

        with (
            patch("skillet._internal.agent.run_codex_cli.which", return_value="/usr/bin/codex"),
            patch("skillet._internal.agent.run_codex_cli.create_subprocess_exec", exec_mock),
        ):
            result = await run_codex_cli(["hi"])

        assert result.text == "done"
        assert result.tool_calls == [{"name": "command_execution", "input": {"command": "ls"}}]

    @pytest.mark.asyncio
    async def it_builds_the_exec_command_with_json_and_sandbox():
        from skillet._internal.agent.run_codex_cli import run_codex_cli

        proc = _FakeProc(_stream("ok", thread_id="t1"))
        exec_mock = AsyncMock(return_value=cast("object", proc))

        with (
            patch("skillet._internal.agent.run_codex_cli.which", return_value="/usr/bin/codex"),
            patch("skillet._internal.agent.run_codex_cli.create_subprocess_exec", exec_mock),
        ):
            await run_codex_cli(["hi"], cwd="/sandbox")

        cmd = exec_mock.call_args.args
        assert cmd[0] == "codex"
        assert cmd[1] == "exec"
        assert "--json" in cmd
        assert "--skip-git-repo-check" in cmd
        assert "-s" in cmd
        assert "workspace-write" in cmd
        assert "-C" in cmd
        assert "/sandbox" in cmd
        assert cmd[-1] == "hi"

    @pytest.mark.asyncio
    async def it_omits_cwd_flag_when_no_cwd():
        from skillet._internal.agent.run_codex_cli import run_codex_cli

        proc = _FakeProc(_stream("ok", thread_id="t1"))
        exec_mock = AsyncMock(return_value=cast("object", proc))

        with (
            patch("skillet._internal.agent.run_codex_cli.which", return_value="/usr/bin/codex"),
            patch("skillet._internal.agent.run_codex_cli.create_subprocess_exec", exec_mock),
        ):
            await run_codex_cli(["hi"])

        cmd = exec_mock.call_args.args
        assert "-C" not in cmd

    @pytest.mark.asyncio
    async def it_resumes_session_on_subsequent_turns():
        from skillet._internal.agent.run_codex_cli import run_codex_cli

        procs = [
            _FakeProc(_stream("turn1", thread_id="sess-abc")),
            _FakeProc(_stream("turn2")),
        ]
        exec_mock = AsyncMock(side_effect=[cast("object", p) for p in procs])

        with (
            patch("skillet._internal.agent.run_codex_cli.which", return_value="/usr/bin/codex"),
            patch("skillet._internal.agent.run_codex_cli.create_subprocess_exec", exec_mock),
        ):
            result = await run_codex_cli(["one", "two"])

        first_cmd = exec_mock.call_args_list[0].args
        second_cmd = exec_mock.call_args_list[1].args
        assert "resume" not in first_cmd
        assert second_cmd[1] == "exec"
        assert "resume" in second_cmd
        assert "sess-abc" in second_cmd
        assert "--json" in second_cmd
        assert result.text == "turn2"

    @pytest.mark.asyncio
    async def it_passes_cwd_and_env_and_devnull_stdin_to_subprocess():
        from asyncio.subprocess import DEVNULL

        from skillet._internal.agent.run_codex_cli import run_codex_cli

        proc = _FakeProc(_stream("ok", thread_id="t1"))
        exec_mock = AsyncMock(return_value=cast("object", proc))

        with (
            patch("skillet._internal.agent.run_codex_cli.which", return_value="/usr/bin/codex"),
            patch("skillet._internal.agent.run_codex_cli.create_subprocess_exec", exec_mock),
        ):
            await run_codex_cli(["hi"], cwd="/sandbox", env={"HOME": "/tmp/home"})

        assert exec_mock.call_args.kwargs["cwd"] == "/sandbox"
        assert exec_mock.call_args.kwargs["env"] == {"HOME": "/tmp/home"}
        assert exec_mock.call_args.kwargs["stdin"] == DEVNULL

    @pytest.mark.asyncio
    async def it_raises_loudly_on_turn_failed():
        from skillet._internal.agent.run_codex_cli import run_codex_cli

        proc = _FakeProc(_stream(thread_id="t1", error="model not supported"))
        exec_mock = AsyncMock(return_value=cast("object", proc))

        with (
            patch("skillet._internal.agent.run_codex_cli.which", return_value="/usr/bin/codex"),
            patch("skillet._internal.agent.run_codex_cli.create_subprocess_exec", exec_mock),
            pytest.raises(RuntimeError, match=r"codex.*model not supported"),
        ):
            await run_codex_cli(["hi"])

    @pytest.mark.asyncio
    async def it_raises_on_nonzero_exit_without_text():
        from skillet._internal.agent.run_codex_cli import run_codex_cli

        proc = _FakeProc(b"", returncode=1, stderr=b"boom")
        exec_mock = AsyncMock(return_value=cast("object", proc))

        with (
            patch("skillet._internal.agent.run_codex_cli.which", return_value="/usr/bin/codex"),
            patch("skillet._internal.agent.run_codex_cli.create_subprocess_exec", exec_mock),
            pytest.raises(RuntimeError, match=r"codex exited with code 1.*boom"),
        ):
            await run_codex_cli(["hi"])
