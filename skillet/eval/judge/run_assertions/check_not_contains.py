"""Check that response does not contain a value (case-insensitive)."""


def check_not_contains(value: str, response_lower: str, **_: object) -> str | None:
    if value.lower() in response_lower:
        return f"not_contains: expected response NOT to contain '{value}'"
    return None
