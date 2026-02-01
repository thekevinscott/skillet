"""Centralized Claude SDK wrapper with automatic caching."""

import json
import sys
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

from .cache import CacheManager


def _parse_json_response(text: str) -> dict | None:
    """Parse JSON from Claude response, handling markdown code blocks."""
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) < 2:
            return None
        text = parts[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


async def query_json(
    prompt: str,
    *,
    cache_dir: Path | None = None,
    skip_cache: bool = False,
    verbose: bool = False,
) -> tuple[dict | None, bool]:
    """Query Claude and return parsed JSON response with automatic caching.

    Caching is based on the full prompt hash, so identical prompts return
    cached results. Different prompts (even with same content) are cached
    separately.

    Returns a tuple of (result, from_cache) where from_cache is True if the
    result was retrieved from cache.
    """
    cache = CacheManager(cache_dir=cache_dir, skip_cache=skip_cache) if cache_dir else None

    # Check cache first
    if cache:
        cached = cache.get(prompt)
        if cached is not None:
            return cached, True

    # Query Claude
    options = ClaudeAgentOptions(
        allowed_tools=[],
        max_turns=1,
    )

    result = None
    try:
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, ResultMessage):
                if message.is_error:
                    if verbose:
                        print(f"Error: {message.result}", file=sys.stderr)
                    return None, False
                if message.result:
                    result = _parse_json_response(message.result)
                    if result is None and verbose:
                        print(f"Failed to parse JSON: {message.result[:200]}...", file=sys.stderr)
    except Exception as e:
        if verbose:
            print(f"Query error: {e}", file=sys.stderr)
        return None, False

    # Cache successful result
    if result is not None and cache:
        cache.set(prompt, result)

    return result, False
