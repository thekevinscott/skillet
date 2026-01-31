"""Shared utilities for skill collection."""

import sys


def status(msg: str):
    """Print a status message, overwriting the current line."""
    sys.stdout.write(f"\r\033[K{msg}")
    sys.stdout.flush()
