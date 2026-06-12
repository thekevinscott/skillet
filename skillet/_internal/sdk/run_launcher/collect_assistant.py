"""Extract text and tool calls from a stream-json ``assistant`` event."""


def collect_assistant(event: dict, text_parts: list[str], tool_calls: list[dict]) -> None:
    """Pull text and tool_use blocks out of one stream-json ``assistant`` event."""
    content = event.get("message", {}).get("content", [])
    for block in content if isinstance(content, list) else []:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text":
            text_parts.append(block.get("text", ""))
        elif block.get("type") == "tool_use":
            tool_calls.append({"name": block.get("name", ""), "input": block.get("input", {})})
