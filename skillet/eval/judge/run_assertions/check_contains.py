"""Check that response contains a value (case-insensitive)."""


def check_contains(value: str, response_lower: str, **_: object) -> str | None:
    if value.lower() not in response_lower:
        return f"contains: expected response to contain '{value}'"
    return None
