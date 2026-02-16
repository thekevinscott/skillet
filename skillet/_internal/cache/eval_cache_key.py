"""Generate cache keys for evals."""

from .hash_content import hash_content


def eval_cache_key(eval_source: str, eval_content: str) -> str:
    """Return cache key for an eval: <filename>-<content-hash>."""
    content_hash = hash_content(eval_content)
    # Remove .yaml extension for cleaner key
    name = eval_source.replace(".yaml", "")
    return f"{name}-{content_hash}"
