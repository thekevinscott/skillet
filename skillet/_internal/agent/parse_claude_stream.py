"""Parse a single turn of `claude -p --output-format stream-json` output."""

import json


def _decode_line(line: str) -> dict | None:
    """Decode one stream-json line into a dict, or None if blank/malformed."""
    line = line.strip()
    if not line:
        return None
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        return None
    return event if isinstance(event, dict) else None


def _collect_assistant_blocks(event: dict, text_parts: list[str], tool_calls: list[dict]) -> None:
    """Append text and tool-use content blocks from one assistant event."""
    for block in event.get("message", {}).get("content", []):
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text":
            text_parts.append(block.get("text", ""))
        elif block.get("type") == "tool_use":
            tool_calls.append({"name": block.get("name"), "input": block.get("input")})


def parse_claude_stream(stdout: str) -> tuple[str, list[dict], str | None]:
    """Parse one turn of Claude CLI stream-json into text, tool calls, and session id.

    The CLI emits one JSON object per line. The shapes we care about:

    - ``{"type": "system", "subtype": "init", "session_id": ...}`` — the session id
      used to resume the conversation on subsequent turns.
    - ``{"type": "assistant", "message": {"content": [...]}}`` — assistant turns whose
      content blocks are ``{"type": "text", "text": ...}`` or
      ``{"type": "tool_use", "name": ..., "input": ...}``.
    - ``{"type": "result", "result": ...}`` — the final result text, used as a fallback
      when no assistant text block was emitted.

    Malformed lines are skipped. Returns ``(text, tool_calls, session_id)``.
    """
    text_parts: list[str] = []
    tool_calls: list[dict] = []
    session_id: str | None = None
    result_text: str | None = None

    for line in stdout.splitlines():
        event = _decode_line(line)
        if event is None:
            continue

        event_type = event.get("type")
        if event_type == "system" and event.get("subtype") == "init":
            if event.get("session_id"):
                session_id = str(event["session_id"])
        elif event_type == "assistant":
            _collect_assistant_blocks(event, text_parts, tool_calls)
        elif event_type == "result":
            result = event.get("result")
            if isinstance(result, str):
                result_text = result

    text = "".join(text_parts).strip()
    if not text and result_text:
        text = result_text.strip()

    return text, tool_calls, session_id
