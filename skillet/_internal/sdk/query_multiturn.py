"""Multi-turn conversation queries using Claude SDK."""

import sys
from typing import Any

import claude_agent_sdk
from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, TextBlock, ToolUseBlock

from .query_result import QueryResult


async def query_multiturn(  # noqa: C901 - complexity from SDK protocol handling
    prompts: list[str],
    **options: Any,
) -> QueryResult:
    """Run a multi-turn conversation and return the final assistant response."""
    opts = ClaudeAgentOptions(**options, stderr=lambda line: print(line, file=sys.stderr))
    session_id: str | None = None
    response_text = ""
    all_tool_calls: list[dict] = []

    for p in prompts:
        response_text = ""

        # Resume session for subsequent turns
        if session_id:
            opts.resume = session_id

        async for message in claude_agent_sdk.query(prompt=p, options=opts):
            # Capture session ID from init message
            if hasattr(message, "subtype") and message.subtype == "init":
                if hasattr(message, "session_id"):
                    session_id = str(message.session_id)
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
