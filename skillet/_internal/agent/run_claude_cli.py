"""Run a prompt (or multi-turn conversation) through the Claude Code CLI."""

from asyncio import create_subprocess_exec
from asyncio.subprocess import PIPE
from shutil import which

from skillet._internal.sdk.query_result import QueryResult

from .parse_claude_stream import parse_claude_stream

# Headless `-p` runs cannot answer interactive permission prompts, so tools are
# pre-approved. Evals already run in an isolated, throwaway HOME.
_BASE_CMD = [
    "claude",
    "-p",
    "--output-format",
    "stream-json",
    "--verbose",
    "--permission-mode",
    "bypassPermissions",
]


async def run_claude_cli(
    prompts: list[str],
    *,
    allowed_tools: list[str] | None = None,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> QueryResult:
    """Drive the `claude` CLI as the agent under test and return its response.

    Each prompt is run as a separate `claude -p` process; subsequent turns resume
    the prior session via ``--resume`` so multi-turn evals keep their context.
    Run in ``cwd`` so the CLI auto-loads ``.claude/skills`` from the eval sandbox.

    Args:
        prompts: One prompt per turn.
        allowed_tools: Tools to pre-approve (passed to ``--allowedTools``).
        cwd: Working directory for the CLI (the eval sandbox).
        env: Environment for the subprocess (e.g. an isolated ``HOME``).

    Raises:
        RuntimeError: If the `claude` CLI is missing from PATH, or a turn exits
            non-zero without producing any text.
    """
    if which("claude") is None:
        raise RuntimeError(
            "The 'claude' CLI was not found on PATH. Install Claude Code to run "
            "evals with --agent claude."
        )

    session_id: str | None = None
    response_text = ""
    all_tool_calls: list[dict] = []

    for prompt in prompts:
        cmd = list(_BASE_CMD)
        if allowed_tools:
            cmd += ["--allowedTools", *allowed_tools]
        if session_id:
            cmd += ["--resume", session_id]
        cmd.append(prompt)

        proc = await create_subprocess_exec(
            *cmd,
            cwd=cwd,
            env=env,
            stdout=PIPE,
            stderr=PIPE,
        )
        stdout, stderr = await proc.communicate()

        text, tool_calls, turn_session_id = parse_claude_stream(stdout.decode())

        if proc.returncode != 0 and not text:
            err = stderr.decode().strip()
            raise RuntimeError(
                f"claude exited with code {proc.returncode}" + (f": {err}" if err else "")
            )

        if turn_session_id:
            session_id = turn_session_id
        response_text = text
        all_tool_calls.extend(tool_calls)

    return QueryResult(text=response_text, tool_calls=all_tool_calls)
