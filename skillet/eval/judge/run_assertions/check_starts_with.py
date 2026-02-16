"""Check that response starts with a value (case-insensitive)."""


def check_starts_with(value: str, response_lower: str, **_: object) -> str | None:
    if not response_lower.startswith(value.lower()):
        return f"starts_with: expected response to start with '{value}'"
    return None
