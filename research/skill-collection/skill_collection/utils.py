"""Shared utilities for skill collection."""

import sys


def status(msg: str):
    """Print a status message, overwriting the current line."""
    sys.stdout.write(f"\r\033[K{msg}")
    sys.stdout.flush()


def truncate_url(url: str, max_len: int = 60) -> str:
    """Truncate URL for display, keeping the end visible."""
    display = url.removeprefix("https://github.com/")
    if len(display) <= max_len:
        return display
    keep = (max_len - 3) // 2
    return display[:keep] + "..." + display[-keep:]


def truncate_text(text: str, max_len: int = 120) -> str:
    """Truncate text to max length, breaking at word boundary."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rsplit(" ", 1)[0] + "..."
