"""Structured output queries using Claude SDK."""

from typing import Any

import claude_agent_sdk
from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ResultMessage, ToolUseBlock
from pydantic import BaseModel, ValidationError

from .stderr import _stderr_callback


class StructuredOutputError(Exception):
    """Raised when structured output contains unexpected formatting."""

    pass


def _validate_with_unwrap[T: BaseModel](model: type[T], data: Any) -> T:
    """Validate data against a Pydantic model, unwrapping single-key wrappers.

    LLMs sometimes wrap structured output in an extra object layer like
    {"output": {...}} or {"result": {...}}. When validation fails and the
    data is a single-key dict whose value is itself a dict, try validating
    the inner value before giving up.
    """
    try:
        return model.model_validate(data)
    except ValidationError:
        if isinstance(data, dict) and len(data) == 1:
            inner = next(iter(data.values()))
            if isinstance(inner, dict):
                return model.model_validate(inner)
        raise


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
                    return _validate_with_unwrap(model, block.input)

        if isinstance(message, ResultMessage):
            # Fallback: if the SDK ever populates structured_output directly
            if message.structured_output is not None:
                return _validate_with_unwrap(model, message.structured_output)

            # Canary: check if result contains backticks (shouldn't happen with structured output)
            if message.result and "```" in message.result:
                raise StructuredOutputError(
                    "Response contains markdown code fences. "
                    "This indicates structured output was not properly configured. "
                    f"Raw result: {message.result[:200]}..."
                )

    raise ValueError("No structured output returned from query")
