"""Iterate over blocks from a Claude query with optional type filtering."""

import sys
from typing import Any, TypeVar

from claude_agent_sdk import ClaudeAgentOptions, query

from skillet._internal.types import matches_type

T = TypeVar("T")


async def for_query(
    prompt: str,
    message_type: type[T] | None = None,
    block_type: type[T] | None = None,
    **options: Any,
):
    """Iterate over blocks from a Claude query with optional type filtering."""
    opts = ClaudeAgentOptions(**options, stderr=lambda line: print(line, file=sys.stderr))
    async for message in query(prompt=prompt, options=opts):
        if not message_type or matches_type(message, message_type):
            if not hasattr(message, "content"):
                continue
            for block in message.content:  # type: ignore[union-attr]
                if not block_type or matches_type(block, block_type):
                    yield block
