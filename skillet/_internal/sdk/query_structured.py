"""Structured output queries using Claude SDK."""

from typing import Any

import claude_agent_sdk
from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ResultMessage, ToolUseBlock
from pydantic import BaseModel

from .stderr import _stderr_callback


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

    async for message in claude_agent_sdk.query(prompt=prompt, options=opts):
        # The SDK delivers structured output via a synthetic StructuredOutput
        # tool call in an AssistantMessage, not via ResultMessage.structured_output
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock) and block.name == "StructuredOutput":
                    return model.model_validate(block.input)

        if isinstance(message, ResultMessage):
            # Fallback: if the SDK ever populates structured_output directly
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
