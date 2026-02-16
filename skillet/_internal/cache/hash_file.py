"""Hash file contents."""

from pathlib import Path

from .hash_content import hash_content


def hash_file(path: Path) -> str:
    """Return short md5 hash of file contents."""
    return hash_content(path.read_text())
