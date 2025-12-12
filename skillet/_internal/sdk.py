"""Claude SDK helpers."""

from typing import TypeVar

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, TextBlock, query

from .types import matches_type

T = TypeVar("T")


async def for_query(
    prompt: str,
    message_type: type[T] | None = None,
    block_type: type[T] | None = None,
    **options: ClaudeAgentOptions,
):
    """Iterate over blocks from a Claude query with optional type filtering."""
    async for message in query(prompt=prompt, options=ClaudeAgentOptions(**options)):
        if not message_type or matches_type(message, message_type):
            for block in message.content:
                if not block_type or matches_type(block, block_type):
                    yield block


async def query_assistant_text(prompt: str, **options: ClaudeAgentOptions) -> str:
    """Query Claude and return just the assistant's text response."""
    result = ""
    async for block in for_query(prompt, AssistantMessage, TextBlock, **options):
        result += block.text
    return result.strip()
