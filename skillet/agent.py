"""The agent under test — the CLI that both runs the skill and judges the result."""

from enum import StrEnum


class Agent(StrEnum):
    """A coding agent selectable at invocation via the required ``--agent`` flag.

    Each agent is driven through its own external CLI; skillet has no Python
    dependency on either and never silently falls back to one.
    """

    CLAUDE = "claude"
    CODEX = "codex"
