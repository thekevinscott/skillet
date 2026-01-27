"""Sanitize strings for use as filenames."""

import re


def get_name_part(candidate_name: str, index: int) -> str:
    """Sanitize a candidate name for use as a filename stem, with numbered fallback."""
    sanitized = re.sub(r"[^\w-]", "-", candidate_name)
    sanitized = re.sub(r"-{2,}", "-", sanitized).strip("-")
    return sanitized or f"candidate-{index + 1}"
