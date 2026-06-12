"""Dispatch a multi-turn agent run to the native Claude SDK or a launcher command."""

from typing import Any

from .query_result import QueryResult
from .run_claude import run_claude
from .run_launcher import run_launcher


async def query_multiturn(
    prompts: list[str],
    *,
    launcher: str | None = None,
    **options: Any,
) -> QueryResult:
    """Run a multi-turn conversation and return the final assistant response.

    With no ``launcher`` the agent under test is the native Claude Agent SDK.
    When ``launcher`` is set, the prompt is run through that command instead
    (see :func:`run_launcher`); the judge always stays on the Claude SDK.
    """
    if launcher:
        return await run_launcher(prompts, launcher=launcher, **options)
    return await run_claude(prompts, **options)
