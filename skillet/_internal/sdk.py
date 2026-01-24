"""Claude SDK helpers."""

import sys
from dataclasses import dataclass, field
from typing import Any, TypeVar

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    query,
)
from pydantic import BaseModel

from .types import matches_type


@dataclass
class QueryResult:
    """Result from a query with both text and tool calls."""

    text: str
    tool_calls: list[dict] = field(default_factory=list)


T = TypeVar("T")


def _stderr_callback(line: str) -> None:
    """Print stderr output from Claude CLI."""
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
    """Query Claude and return just the assistant's text response."""
    result = ""
    async for block in for_query(prompt, AssistantMessage, TextBlock, **options):
        result += block.text
    return result.strip()


class StructuredOutputError(Exception):
    """Raised when structured output contains unexpected formatting."""

    pass


async def query_structured[T: BaseModel](prompt: str, model: type[T], **options: Any) -> T:
    """Query Claude and return a validated Pydantic model.

    Uses the Claude Agent SDK's structured output feature to guarantee
    schema-compliant JSON responses without markdown wrapping. Raises
    StructuredOutputError if backticks are detected (canary for misconfiguration).
    """
    if not (isinstance(model, type) and issubclass(model, BaseModel)):
        raise TypeError(f"model must be a Pydantic BaseModel subclass, got {type(model)}")

    opts = ClaudeAgentOptions(
        output_format={
            "type": "json_schema",
            "schema": model.model_json_schema(),
        },
        stderr=_stderr_callback,
        **options,
    )

    async for message in query(prompt=prompt, options=opts):
        if isinstance(message, ResultMessage):
            if message.structured_output is not None:
                return model.model_validate(message.structured_output)

            # Canary: check if result contains backticks (shouldn't happen with structured output)
            if message.result and "```" in message.result:
                raise StructuredOutputError(
                    "Response contains markdown code fences. "
                    "This indicates structured output was not properly configured. "
                    f"Raw result: {message.result[:200]}..."
                )

    raise ValueError("No structured output returned from query")


async def query_multiturn(  # noqa: C901 - complexity from SDK protocol handling
    prompts: list[str],
    **options: Any,
) -> QueryResult:
    """Run a multi-turn conversation and return the final assistant response.

    Args:
        prompts: List of prompts to send sequentially, resuming the session
        **options: Options passed to ClaudeAgentOptions

    Returns:
        QueryResult with text and all tool calls made during the conversation
    """
    opts = ClaudeAgentOptions(**options, stderr=_stderr_callback)
    session_id: str | None = None
    response_text = ""
    all_tool_calls: list[dict] = []

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
                    elif isinstance(block, ToolUseBlock):
                        all_tool_calls.append(
                            {
                                "name": block.name,
                                "input": block.input,
                            }
                        )

    return QueryResult(
        text=response_text.strip() if response_text else "",
        tool_calls=all_tool_calls,
    )
