"""Hash string content."""

import hashlib


def hash_content(content: str) -> str:
    """Return short md5 hash of content."""
    return hashlib.md5(content.encode()).hexdigest()[:12]
