"""Check that a named tool was called."""


def check_tool_called(value: str, tool_names: set[str], **_: object) -> str | None:
    if value not in tool_names:
        return f"tool_called: expected tool '{value}' to be called"
    return None
