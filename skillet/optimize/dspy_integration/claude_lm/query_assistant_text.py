"""Query Claude and return just the assistant's text response."""

from typing import Any

from claude_agent_sdk import AssistantMessage, TextBlock

from .for_query import for_query


async def query_assistant_text(prompt: str, **options: Any) -> str:
    """Query Claude and return just the assistant's text response.

    This is used by DSPy integration which expects raw text completions.
    For structured output, use query_structured instead.
    """
    result = ""
    async for block in for_query(prompt, AssistantMessage, TextBlock, **options):
        result += block.text
    return result.strip()
