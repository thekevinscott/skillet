"""Hash directory contents."""

from pathlib import Path

from .hash_content import hash_content
from .hash_file import hash_file


def hash_directory(path: Path) -> str:
    """Return hash of all files in directory (sorted, concatenated)."""
    if not path.is_dir():
        return hash_file(path)

    contents = []
    for f in sorted(path.rglob("*")):
        if f.is_file():
            contents.append(f"{f.relative_to(path)}:{f.read_text()}")

    return hash_content("\n".join(contents))
