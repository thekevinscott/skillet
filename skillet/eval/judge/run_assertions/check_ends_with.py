"""Check that response ends with a value (case-insensitive)."""


def check_ends_with(value: str, response_lower: str, **_: object) -> str | None:
    if not response_lower.rstrip().endswith(value.lower()):
        return f"ends_with: expected response to end with '{value}'"
    return None
