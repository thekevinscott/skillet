"""Registry of agent-harness adapters for the agent under test.

Each adapter is an async callable ``(prompts, **options) -> QueryResult``. To
add a new connector, add one entry to :data:`HARNESS_ADAPTERS` — Codex and any
other lite-harness backend are one line via :func:`_lite_harness_adapter`.
"""

from collections.abc import Awaitable, Callable
from typing import Any

from skillet.errors import UnknownHarnessError

from ..query_result import QueryResult
from . import lite_harness
from .claude import run_claude

HarnessAdapter = Callable[..., Awaitable[QueryResult]]

DEFAULT_HARNESS = "claude"


def _lite_harness_adapter(harness_name: str) -> HarnessAdapter:
    """Build an adapter that routes the run to lite-harness under ``harness_name``."""

    async def adapter(prompts: list[str], **options: Any) -> QueryResult:
        return await lite_harness.run_lite_harness(prompts, harness=harness_name, **options)

    return adapter


# Skillet harness name -> adapter. One entry per supported connector.
HARNESS_ADAPTERS: dict[str, HarnessAdapter] = {
    "claude": run_claude,
    "codex": _lite_harness_adapter("codex"),
}

HARNESS_NAMES = frozenset(HARNESS_ADAPTERS)


def get_adapter(harness: str) -> HarnessAdapter:
    """Return the adapter for ``harness``, or raise ``UnknownHarnessError``."""
    try:
        return HARNESS_ADAPTERS[harness]
    except KeyError:
        known = ", ".join(sorted(HARNESS_NAMES))
        raise UnknownHarnessError(
            f"Unknown harness {harness!r}. Available harnesses: {known}."
        ) from None
