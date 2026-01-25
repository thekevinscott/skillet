"""Raw text query helper for DSPy integration.

This module provides query_assistant_text which returns raw text responses
from Claude. It's used by DSPy's ClaudeAgentLM since DSPy expects raw text
completions rather than structured output.

For structured JSON responses, use query_structured from skillet._internal.sdk.
"""

from typing import Any, TypeVar

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, TextBlock, query

from skillet._internal.types import matches_type

T = TypeVar("T")


def _stderr_callback(line: str) -> None:
    """Print stderr output from Claude CLI."""
    import sys

    print(line, file=sys.stderr)


async def for_query(
    prompt: str,
    message_type: type[T] | None = None,
    block_type: type[T] | None = None,
    **options: Any,
):
    """Iterate over blocks from a Claude query with optional type filtering."""
    opts = ClaudeAgentOptions(**options, stderr=_stderr_callback)
    async for message in query(prompt=prompt, options=opts):
        if not message_type or matches_type(message, message_type):
            if not hasattr(message, "content"):
                continue
            for block in message.content:  # type: ignore[union-attr]
                if not block_type or matches_type(block, block_type):
                    yield block


async def query_assistant_text(prompt: str, **options: Any) -> str:
    """Query Claude and return just the assistant's text response.

    This is used by DSPy integration which expects raw text completions.
    For structured output, use query_structured instead.
    """
    result = ""
    async for block in for_query(prompt, AssistantMessage, TextBlock, **options):
        result += block.text
    return result.strip()
