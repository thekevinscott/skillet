"""Dispatch a multi-turn agent run to the selected harness adapter."""

from typing import Any

from .harness import DEFAULT_HARNESS, get_adapter
from .query_result import QueryResult


async def query_multiturn(
    prompts: list[str],
    *,
    harness: str = DEFAULT_HARNESS,
    **options: Any,
) -> QueryResult:
    """Run a multi-turn conversation on the selected harness and return the final response.

    ``harness`` selects which agent harness executes the prompts (e.g. ``claude``
    or ``codex``); the judge always stays on the Claude Agent SDK regardless.
    """
    adapter = get_adapter(harness)
    return await adapter(prompts, **options)
