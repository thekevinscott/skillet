"""Shared utilities for skill collection."""

import signal
import sys
from pathlib import Path


def setup_sigpipe_handler():
    """Handle broken pipe gracefully (e.g., when piping to head)."""
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)


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


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )


def escape_table_cell(text: str) -> str:
    """Escape text for use in markdown table cell."""
    # Escape HTML entities first, then pipe characters which break table structure
    return escape_html(text).replace("|", "&#124;")


def truncate_for_analysis(content: str, max_length: int) -> str:
    """Truncate content for LLM analysis, appending truncation marker if needed."""
    if len(content) <= max_length:
        return content
    return content[:max_length] + "\n\n[truncated]"


def resolve_content_path(content_dir: "Path", owner: str, repo: str, ref: str, path: str) -> "Path":
    """Build local content path from GitHub URL components."""
    return content_dir / owner / repo / "blob" / ref / path


def parse_github_url(url: str) -> tuple[str, str, str, str] | None:
    """Parse a GitHub blob URL into (owner, repo, ref, path).

    Example: https://github.com/owner/repo/blob/ref/path/to/file.md
    Returns: ('owner', 'repo', 'ref', 'path/to/file.md')
    """
    if not url.startswith("https://github.com/"):
        return None
    # Remove https://github.com/
    rest = url[19:]
    parts = rest.split("/")
    if len(parts) < 5 or parts[2] != "blob":
        return None
    owner = parts[0]
    repo = parts[1]
    ref = parts[3]
    path = "/".join(parts[4:])
    return owner, repo, ref, path
