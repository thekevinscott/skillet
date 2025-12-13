"""Claude SDK helpers."""

from typing import Any, TypeVar

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, TextBlock, query

from .types import matches_type

T = TypeVar("T")


async def for_query(
    prompt: str,
    message_type: type[T] | None = None,
    block_type: type[T] | None = None,
    **options: Any,
):
    """Iterate over blocks from a Claude query with optional type filtering."""
    async for message in query(prompt=prompt, options=ClaudeAgentOptions(**options)):
        if not message_type or matches_type(message, message_type):
            if not hasattr(message, "content"):
                continue
            for block in message.content:  # type: ignore[union-attr]
                if not block_type or matches_type(block, block_type):
                    yield block


async def query_assistant_text(prompt: str, **options: Any) -> str:
    """Query Claude and return just the assistant's text response."""
    result = ""
    async for block in for_query(prompt, AssistantMessage, TextBlock, **options):
        result += block.text
    return result.strip()


async def query_multiturn(
    prompts: list[str],
    **options: Any,
) -> str:
    """Run a multi-turn conversation and return the final assistant text response.

    Args:
        prompts: List of prompts to send sequentially, resuming the session
        **options: Options passed to ClaudeAgentOptions

    Returns:
        The final assistant response text
    """
    opts = ClaudeAgentOptions(**options)
    session_id: str | None = None
    response_text = ""

    for p in prompts:
        response_text = ""

        # Resume session for subsequent turns
        if session_id:
            opts.resume = session_id

        async for message in query(prompt=p, options=opts):
            # Capture session ID from init message
            if hasattr(message, "subtype") and message.subtype == "init":
                if hasattr(message, "session_id"):
                    session_id = str(message.session_id)  # type: ignore[attr-defined]
                elif hasattr(message, "data"):
                    data = getattr(message, "data", None)
                    if isinstance(data, dict) and "session_id" in data:
                        session_id = str(data["session_id"])

            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_text += block.text

    return response_text.strip() if response_text else ""
