"""Hash string content."""

import hashlib


def hash_content(content: str) -> str:
    """Return short SHA-256 hash of content."""
    return hashlib.sha256(content.encode()).hexdigest()[:12]
