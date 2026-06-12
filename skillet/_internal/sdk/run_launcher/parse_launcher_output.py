"""Parse launcher stdout as Claude Agent SDK stream-json, or plain text."""

import json

from .collect_assistant import collect_assistant


def parse_launcher_output(stdout: str) -> tuple[str, list[dict]]:
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
            collect_assistant(event, text_parts, tool_calls)
        elif event.get("type") == "result":
            structured = True
            if isinstance(event.get("result"), str):
                result_text = event["result"]

    if structured:
        return ("".join(text_parts) or result_text or ""), tool_calls
    return stdout.strip(), []
