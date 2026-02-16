"""Structured output queries using Claude SDK."""

import sys
from typing import Any

import claude_agent_sdk
from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ResultMessage, ToolUseBlock
from pydantic import BaseModel, ValidationError


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


async def query_structured[T: BaseModel](prompt: str, model: type[T], **options: Any) -> T:  # noqa: C901 - complexity from SDK protocol + error deferral
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
        stderr=lambda line: print(line, file=sys.stderr),
        **options,
    )

    # Fully consume the async generator to avoid anyio cancel scope errors.
    # Any exception (raise, break, return) inside `async for` abandons the
    # generator, deferring cleanup to GC which may run in a different
    # asyncio.Task -- triggering RuntimeError from anyio's CancelScope when
    # used under asyncio.gather(). See SDK issues #378, #454.
    #
    # We catch ALL exceptions inside the loop body and defer them until after
    # the generator is fully consumed.
    result: T | None = None
    deferred_error: Exception | None = None

    async for message in claude_agent_sdk.query(prompt=prompt, options=opts):
        if deferred_error is not None:
            continue

        try:
            if result is None and isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, ToolUseBlock) and block.name == "StructuredOutput":
                        result = _validate_with_unwrap(model, block.input)

            if result is None and isinstance(message, ResultMessage):
                if message.structured_output is not None:
                    result = _validate_with_unwrap(model, message.structured_output)

                if message.result and "```" in message.result:
                    deferred_error = StructuredOutputError(
                        "Response contains markdown code fences. "
                        "This indicates structured output was not properly configured. "
                        f"Raw result: {message.result[:200]}..."
                    )
        except Exception as e:
            deferred_error = e

    if deferred_error is not None:
        raise deferred_error

    if result is None:
        raise ValueError("No structured output returned from query")

    return result
