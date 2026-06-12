"""Run the agent under test via an arbitrary launcher command.

``--launcher "<cmd>"`` lets any agent be the agent under test: skillet spawns
the command with the prompt appended as the final argument and reads the
response from stdout (see :func:`parse_launcher_output` for how text and tool
calls are recovered).

This keeps skillet free of per-agent flag lists: options for the agent live in
the launcher command itself.
"""

import asyncio
import shlex
import sys
from typing import Any

from ..query_result import QueryResult
from .parse_launcher_output import parse_launcher_output


async def run_launcher(
    prompts: list[str],
    *,
    launcher: str,
    **options: Any,
) -> QueryResult:
    """Run prompts through a launcher command and return the final response.

    Each prompt is appended to the launcher command as the final argument and
    run as a fresh process (launcher runs don't resume sessions across turns).
    The command runs in ``cwd`` with ``env`` when provided; other Claude-only
    options are ignored.
    """
    base_cmd = shlex.split(launcher)
    if not base_cmd:
        raise ValueError("Launcher command is empty")

    cwd = options.get("cwd")
    env = options.get("env")

    response_text = ""
    all_tool_calls: list[dict] = []

    for p in prompts:
        proc = await asyncio.create_subprocess_exec(
            *base_cmd,
            p,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env,
        )
        stdout_b, stderr_b = await proc.communicate()
        stderr = stderr_b.decode("utf-8", errors="replace")
        if stderr:
            print(stderr, file=sys.stderr)

        response_text, tool_calls = parse_launcher_output(
            stdout_b.decode("utf-8", errors="replace")
        )
        all_tool_calls.extend(tool_calls)

        if proc.returncode != 0 and not response_text:
            raise RuntimeError(
                f"Launcher {launcher!r} exited {proc.returncode}: {stderr.strip()[:500]}"
            )

    return QueryResult(text=response_text.strip(), tool_calls=all_tool_calls)
