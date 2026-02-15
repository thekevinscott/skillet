"""Format tool calls for the LLM judge."""

import json


def format_tool_calls(tool_calls: list[dict]) -> str:
    """Format tool calls for the judge prompt."""
    if not tool_calls:
        return "(no tools used)"

    lines = []
    for call in tool_calls:
        input_data = call.get("input", {})
        input_str = json.dumps(input_data, indent=2)
        lines.append(f"- {call['name']}: {input_str}")

    return "\n".join(lines)
