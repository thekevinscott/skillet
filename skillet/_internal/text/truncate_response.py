"""Truncate response text for preview."""

MAX_RESPONSE_PREVIEW_LENGTH = 500


def truncate_response(text: str | None, max_length: int = MAX_RESPONSE_PREVIEW_LENGTH) -> str:
    """Truncate response text for preview."""
    if not text:
        return ""
    return text[:max_length]
