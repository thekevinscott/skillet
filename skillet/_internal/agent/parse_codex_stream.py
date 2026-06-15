"""Parse a single turn of `codex exec --json` JSONL output."""

import json

# Item types that represent a tool action (vs. text/reasoning/planning items).
_TOOL_ITEM_TYPES = frozenset({"command_execution", "file_change", "mcp_tool_call", "web_search"})

# Item fields that are envelope metadata rather than tool arguments.
_ITEM_META_FIELDS = frozenset({"id", "type", "status"})


def _decode_line(line: str) -> dict | None:
    """Decode one JSONL line into a dict, or None if blank/malformed."""
    line = line.strip()
    if not line:
        return None
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        return None
    return event if isinstance(event, dict) else None


def _parse_completed_item(event: dict) -> tuple[str | None, dict | None]:
    """Classify an ``item.completed`` event into ``(text, tool_call)``.

    Returns ``(text, None)`` for an ``agent_message``, ``(None, tool_call)`` for a
    tool item, and ``(None, None)`` for anything else (reasoning, todo_list, a
    non-``item.completed`` event, or a malformed item). A tool call is
    ``{"name": <item type>, "input": <item minus id/type/status>}``.
    """
    if event.get("type") != "item.completed":
        return None, None
    item = event.get("item")
    if not isinstance(item, dict):
        return None, None
    item_type = item.get("type")
    if item_type == "agent_message":
        return item.get("text", ""), None
    if item_type in _TOOL_ITEM_TYPES:
        tool_input = {k: v for k, v in item.items() if k not in _ITEM_META_FIELDS}
        return None, {"name": item_type, "input": tool_input}
    return None, None


def _extract_error(event: dict) -> str | None:
    """Pull an error message from a ``turn.failed`` or top-level ``error`` event."""
    event_type = event.get("type")
    if event_type == "turn.failed":
        message = event.get("error", {}).get("message")
        return str(message) if message else None
    if event_type == "error" and event.get("message"):
        return str(event["message"])
    return None


def parse_codex_stream(stdout: str) -> tuple[str, list[dict], str | None, str | None]:
    """Parse one turn of ``codex exec --json`` into text, tool calls, id, and error.

    The CLI emits one JSON object per line. The shapes we care about:

    - ``{"type": "thread.started", "thread_id": ...}`` — the thread id used to
      ``resume`` the conversation on subsequent turns.
    - ``{"type": "item.completed", "item": {...}}`` — a completed item. An
      ``agent_message`` item's ``text`` is the assistant's answer (the last one
      wins). ``command_execution``/``file_change``/``mcp_tool_call``/``web_search``
      items become tool calls; ``reasoning``/``todo_list`` and anything else are
      ignored.
    - ``{"type": "turn.failed", "error": {"message": ...}}`` or a top-level
      ``{"type": "error", "message": ...}`` — a hard failure for the turn.

    Malformed lines are skipped. Returns ``(text, tool_calls, thread_id, error)``.
    """
    text = ""
    tool_calls: list[dict] = []
    thread_id: str | None = None
    error: str | None = None

    for line in stdout.splitlines():
        event = _decode_line(line)
        if event is None:
            continue
        if event.get("type") == "thread.started" and event.get("thread_id"):
            thread_id = str(event["thread_id"])
        new_text, tool_call = _parse_completed_item(event)
        if new_text is not None:
            text = new_text
        if tool_call is not None:
            tool_calls.append(tool_call)
        error = _extract_error(event) or error

    return text, tool_calls, thread_id, error
