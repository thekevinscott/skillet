"""Run the agent under test via an arbitrary launcher command.

``--launcher "<cmd>"`` lets any agent be the agent under test: skillet spawns
the command with the prompt appended as the final argument and reads the
response from stdout. If stdout is the Claude Agent SDK's newline-delimited
stream-json (e.g. ``claude -p --output-format stream-json``), text **and** tool
calls are extracted so tool-call assertions keep working; otherwise stdout is
treated as the plain-text response.

This keeps skillet free of per-agent flag lists: options for the agent live in
the launcher command itself.
"""

import asyncio
import json
import shlex
import sys
from typing import Any

from .query_result import QueryResult


def _collect_assistant(event: dict, text_parts: list[str], tool_calls: list[dict]) -> None:
    """Pull text and tool_use blocks out of one stream-json ``assistant`` event."""
    content = event.get("message", {}).get("content", [])
    for block in content if isinstance(content, list) else []:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text":
            text_parts.append(block.get("text", ""))
        elif block.get("type") == "tool_use":
            tool_calls.append({"name": block.get("name", ""), "input": block.get("input", {})})


def _parse_launcher_output(stdout: str) -> tuple[str, list[dict]]:
    """Parse launcher stdout as SDK stream-json, falling back to plain text.

    Returns ``(response_text, tool_calls)``. Stream-json ``assistant`` events
    contribute text and ``tool_use`` blocks; a ``result`` event supplies the
    final text when no assistant text was seen.
    """
    text_parts: list[str] = []
    tool_calls: list[dict] = []
    result_text: str | None = None
    structured = False

    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue

        if event.get("type") == "assistant":
            structured = True
            _collect_assistant(event, text_parts, tool_calls)
        elif event.get("type") == "result":
            structured = True
            if isinstance(event.get("result"), str):
                result_text = event["result"]

    if structured:
        return ("".join(text_parts) or result_text or ""), tool_calls
    return stdout.strip(), []


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

        response_text, tool_calls = _parse_launcher_output(
            stdout_b.decode("utf-8", errors="replace")
        )
        all_tool_calls.extend(tool_calls)

        if proc.returncode != 0 and not response_text:
            raise RuntimeError(
                f"Launcher {launcher!r} exited {proc.returncode}: {stderr.strip()[:500]}"
            )

    return QueryResult(text=response_text.strip(), tool_calls=all_tool_calls)
