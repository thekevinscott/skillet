"""Stderr callback for Claude CLI output."""

import sys


def _stderr_callback(line: str) -> None:
    """Print stderr output from Claude CLI."""
    print(line, file=sys.stderr)
