"""Check that a named tool was not called."""


def check_tool_not_called(value: str, tool_names: set[str], **_: object) -> str | None:
    if value in tool_names:
        return f"tool_not_called: expected tool '{value}' NOT to be called"
    return None
