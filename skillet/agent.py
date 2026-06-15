"""The agent under test — the CLI that both runs the skill and judges the result."""

from enum import StrEnum


class Agent(StrEnum):
    """A coding agent selectable at invocation via the required ``--agent`` flag.

    Each agent is driven through its own external CLI; skillet has no Python
    dependency on either and never silently falls back to one.
    """

    CLAUDE = "claude"
    CODEX = "codex"

    @property
    def dot_dir(self) -> str:
        """The agent's per-user config directory name (``.claude`` / ``.codex``).

        Each CLI auto-discovers skills under ``<cwd>/<dot_dir>/skills`` and reads
        its credentials/config from ``~/<dot_dir>``.
        """
        return f".{self.value}"
